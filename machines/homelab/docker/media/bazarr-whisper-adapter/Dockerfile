FROM golang:1.25-alpine AS build

WORKDIR /src
COPY main.go .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /bazarr-whisper-adapter main.go

FROM alpine:3.22
COPY --from=build /bazarr-whisper-adapter /usr/local/bin/
USER nobody
ENTRYPOINT ["bazarr-whisper-adapter"]
