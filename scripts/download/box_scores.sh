URL="https://www.dropbox.com/scl/fi/nilxew58uliadrnf30v2i/box_scores.zip?rlkey=p5m4l1kidt0fid0xmc6sjcedb&st=dcanqux5&dl=1"
OUT=data/box_scores.zip
curl -Lo $OUT $URL
unzip $OUT -d ./data/
rm $OUT
