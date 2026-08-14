# Deliberately not called USER: the shell exports that already, and an env
# var would silently win over this default.
GH_USER ?= Ner04
PHOTO   ?= assets/passport.png
PYTHON  ?= python3

.PHONY: all portrait infocard heatmap clean

all: portrait infocard heatmap

# Background removal needs rembg, which is a heavy optional dependency.
# Without it prep_photo.py falls back to a plain center-crop.
portrait:
	$(PYTHON) scripts/prep_photo.py --input $(PHOTO) --output assets/prepped.png \
		--trim-bottom 0.34
	$(PYTHON) scripts/make_ascii_svg.py --input assets/prepped.png \
		--output assets/portrait.svg --cols 88 --font-size 8 --line-height 8

infocard:
	$(PYTHON) scripts/make_infocard_svg.py --config data/infocard.json \
		--output assets/infocard.svg

heatmap:
	$(PYTHON) scripts/fetch_contributions.py --user $(GH_USER) \
		--output data/contributions.json
	$(PYTHON) scripts/render_heatmap_svg.py --input data/contributions.json \
		--output assets/heatmap.svg

clean:
	rm -f assets/prepped.png assets/portrait.svg assets/infocard.svg \
		assets/heatmap.svg data/contributions.json
