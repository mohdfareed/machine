package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	listenAddress  = "127.0.0.1:9000"
	maxUploadBytes = int64(1 << 30)
	sampleRate     = 16000
	bytesPerSample = 2
)

var (
	client     = &http.Client{}
	whisperURL = requiredEnv("WHISPER_URL")
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /status", status)
	mux.HandleFunc("POST /asr", asr)
	mux.HandleFunc("POST /detect-language", detectLanguage)

	server := &http.Server{
		Addr:              listenAddress,
		Handler:           mux,
		ReadHeaderTimeout: 30 * time.Second,
	}

	log.Printf("Bazarr Whisper adapter listening on %s", listenAddress)
	log.Fatal(server.ListenAndServe())
}

func requiredEnv(name string) string {
	value := os.Getenv(name)
	if value == "" {
		log.Fatalf("%s must be set", name)
	}
	return value
}

func status(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{
		"status":  "ok",
		"version": "whisper.cpp-adapter",
	})
}

func asr(w http.ResponseWriter, r *http.Request) {
	audio, filename, cleanup, err := bazarrAudio(w, r, false)
	if err != nil {
		writeError(w, err)
		return
	}
	defer cleanup()

	output := r.URL.Query().Get("output")
	if output == "" {
		output = "srt"
	} else if output == "txt" {
		output = "text"
	}

	fields := map[string]string{
		"response_format": output,
		"translate":       fmt.Sprint(r.URL.Query().Get("task") == "translate"),
	}
	if language := r.URL.Query().Get("language"); language != "" {
		fields["language"] = language
	}

	response, err := callWhisper(r, audio, filename, fields)
	if err != nil {
		writeError(w, err)
		return
	}
	defer response.Body.Close()
	copyResponse(w, response)
}

func detectLanguage(w http.ResponseWriter, r *http.Request) {
	audio, filename, cleanup, err := bazarrAudio(w, r, true)
	if err != nil {
		writeError(w, err)
		return
	}
	defer cleanup()

	response, err := callWhisper(r, audio, filename, map[string]string{
		"detect_language": "true",
		"response_format": "verbose_json",
	})
	if err != nil {
		writeError(w, err)
		return
	}
	defer response.Body.Close()

	if response.StatusCode < 200 || response.StatusCode >= 300 {
		copyResponse(w, response)
		return
	}

	var result struct {
		Language                    string             `json:"language"`
		DetectedLanguage            string             `json:"detected_language"`
		DetectedLanguageProbability float64            `json:"detected_language_probability"`
		LanguageProbabilities       map[string]float64 `json:"language_probabilities"`
	}
	if err := json.NewDecoder(response.Body).Decode(&result); err != nil {
		writeError(w, fmt.Errorf("invalid response from whisper.cpp: %w", err))
		return
	}

	code, confidence := mostLikelyLanguage(result.LanguageProbabilities)
	if code == "" {
		writeError(w, errors.New("whisper.cpp did not return a language code"))
		return
	}
	if result.DetectedLanguageProbability > 0 {
		confidence = result.DetectedLanguageProbability
	}
	name := result.DetectedLanguage
	if name == "" {
		name = result.Language
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"confidence":        confidence,
		"detected_language": name,
		"language_code":     code,
	})
}

func bazarrAudio(
	w http.ResponseWriter,
	r *http.Request,
	detectionSample bool,
) (multipart.File, string, func(), error) {
	r.Body = http.MaxBytesReader(w, r.Body, maxUploadBytes)
	if err := r.ParseMultipartForm(16 << 20); err != nil {
		return nil, "", func() {}, fmt.Errorf("invalid audio upload: %w", err)
	}
	cleanupForm := func() {
		if r.MultipartForm != nil {
			r.MultipartForm.RemoveAll()
		}
	}

	source, header, err := r.FormFile("audio_file")
	if err != nil {
		cleanupForm()
		return nil, "", func() {}, errors.New("audio_file is required")
	}

	if strings.EqualFold(r.URL.Query().Get("encode"), "true") {
		return source, header.Filename, func() {
			source.Close()
			cleanupForm()
		}, nil
	}

	wav, err := rawPCMToWAV(source, detectionSample)
	source.Close()
	if err != nil {
		cleanupForm()
		return nil, "", func() {}, err
	}

	return wav, replaceExtension(header.Filename, ".wav"), func() {
		name := wav.Name()
		wav.Close()
		os.Remove(name)
		cleanupForm()
	}, nil
}

func rawPCMToWAV(source multipart.File, detectionSample bool) (*os.File, error) {
	wav, err := os.CreateTemp("", "bazarr-whisper-*.wav")
	if err != nil {
		return nil, fmt.Errorf("create temporary WAV: %w", err)
	}
	fail := func(err error) (*os.File, error) {
		name := wav.Name()
		wav.Close()
		os.Remove(name)
		return nil, err
	}

	if _, err := wav.Write(make([]byte, 44)); err != nil {
		return fail(fmt.Errorf("write WAV header: %w", err))
	}

	var written int64
	if detectionSample {
		written, err = copyDetectionSample(wav, source)
	} else {
		written, err = io.Copy(wav, source)
	}
	if err != nil {
		return fail(fmt.Errorf("write WAV audio: %w", err))
	}
	if written == 0 {
		return fail(errors.New("audio_file is empty"))
	}
	if written > int64(^uint32(0))-36 {
		return fail(errors.New("audio_file is too large for WAV"))
	}

	if _, err := wav.Seek(0, io.SeekStart); err != nil {
		return fail(fmt.Errorf("seek temporary WAV: %w", err))
	}
	if _, err := wav.Write(wavHeader(uint32(written))); err != nil {
		return fail(fmt.Errorf("finalize WAV header: %w", err))
	}
	if _, err := wav.Seek(0, io.SeekStart); err != nil {
		return fail(fmt.Errorf("rewind temporary WAV: %w", err))
	}
	return wav, nil
}

func copyDetectionSample(destination io.Writer, source multipart.File) (int64, error) {
	size, err := source.Seek(0, io.SeekEnd)
	if err != nil {
		return 0, err
	}
	const windowBytes = int64(20 * sampleRate * bytesPerSample)
	if size <= 3*windowBytes {
		if _, err := source.Seek(0, io.SeekStart); err != nil {
			return 0, err
		}
		return io.Copy(destination, source)
	}

	var written int64
	for _, position := range []float64{0.10, 0.50, 0.85} {
		start := int64(float64(size)*position) - windowBytes/2
		if start < 0 {
			start = 0
		} else if start+windowBytes > size {
			start = size - windowBytes
		}
		start -= start % bytesPerSample
		if _, err := source.Seek(start, io.SeekStart); err != nil {
			return written, err
		}
		copied, err := io.CopyN(destination, source, windowBytes)
		written += copied
		if err != nil {
			return written, err
		}
	}
	return written, nil
}

func wavHeader(dataSize uint32) []byte {
	header := bytes.NewBuffer(make([]byte, 0, 44))
	header.WriteString("RIFF")
	binary.Write(header, binary.LittleEndian, dataSize+36)
	header.WriteString("WAVEfmt ")
	binary.Write(header, binary.LittleEndian, uint32(16))
	binary.Write(header, binary.LittleEndian, uint16(1))
	binary.Write(header, binary.LittleEndian, uint16(1))
	binary.Write(header, binary.LittleEndian, uint32(sampleRate))
	binary.Write(header, binary.LittleEndian, uint32(sampleRate*bytesPerSample))
	binary.Write(header, binary.LittleEndian, uint16(bytesPerSample))
	binary.Write(header, binary.LittleEndian, uint16(bytesPerSample*8))
	header.WriteString("data")
	binary.Write(header, binary.LittleEndian, dataSize)
	return header.Bytes()
}

func callWhisper(
	r *http.Request,
	audio io.Reader,
	filename string,
	fields map[string]string,
) (*http.Response, error) {
	bodyReader, bodyWriter := io.Pipe()
	multipartWriter := multipart.NewWriter(bodyWriter)

	go func() {
		part, err := multipartWriter.CreateFormFile("file", filename)
		if err == nil {
			_, err = io.Copy(part, audio)
		}
		for name, value := range fields {
			if err == nil {
				err = multipartWriter.WriteField(name, value)
			}
		}
		if closeErr := multipartWriter.Close(); err == nil {
			err = closeErr
		}
		bodyWriter.CloseWithError(err)
	}()

	request, err := http.NewRequestWithContext(r.Context(), http.MethodPost, whisperURL, bodyReader)
	if err != nil {
		return nil, err
	}
	request.Header.Set("Content-Type", multipartWriter.FormDataContentType())
	response, err := client.Do(request)
	if err != nil {
		return nil, fmt.Errorf("connect to whisper.cpp: %w", err)
	}
	return response, nil
}

func mostLikelyLanguage(probabilities map[string]float64) (string, float64) {
	var code string
	var confidence float64
	for candidate, probability := range probabilities {
		if probability > confidence {
			code = candidate
			confidence = probability
		}
	}
	return code, confidence
}

func replaceExtension(name, extension string) string {
	return strings.TrimSuffix(name, filepath.Ext(name)) + extension
}

func copyResponse(w http.ResponseWriter, response *http.Response) {
	if contentType := response.Header.Get("Content-Type"); contentType != "" {
		w.Header().Set("Content-Type", contentType)
	}
	w.WriteHeader(response.StatusCode)
	io.Copy(w, response.Body)
}

func writeJSON(w http.ResponseWriter, statusCode int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(value)
}

func writeError(w http.ResponseWriter, err error) {
	log.Print(err)
	writeJSON(w, http.StatusBadGateway, map[string]string{"error": err.Error()})
}
