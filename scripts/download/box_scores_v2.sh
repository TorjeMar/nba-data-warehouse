URL="https://www.dropbox.com/scl/fi/t921jmfdwm0skbx842xo6/box_scores.jsonl.zip?rlkey=lyzr1vqkehiraibj0kd2tnysz&st=plfnp83r&dl=1"
OUT=data/box2/box_scores.zip
curl -Lo $OUT $URL
unzip $OUT -d ./data/box2/
rm $OUT
