# get the latest release wheel url from github

repo="mohdfareed/machine"
download_url=$(curl -s https://api.github.com/repos/$repo/releases/latest | \
grep "browser_download_url" | grep ".whl" | cut -d '"' -f 4)
echo $download_url
