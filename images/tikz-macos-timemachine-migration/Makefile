.PHONY: all pdf png clean distclean

# Usage:
#   make            # build PNG (default)
#   make png        # build PNG from TEX
#   make pdf        # build PDF with xelatex (via latexmk)
#   make clean      # remove aux files
#   make distclean  # remove aux + PDF/PNG

# Main source (standalone TikZ)
# Avoid TEX env var clash by using SRC_TEX
SRC_TEX ?= macos-timemachine-migration.tex
OUT_BASE := $(basename $(SRC_TEX))
OUT_PDF  := $(OUT_BASE).pdf
OUT_PNG  := $(OUT_BASE).png

# Build options
DPI ?= 300
LATEXMK ?= latexmk
XELATEX ?= xelatex

all: png

pdf: $(OUT_PDF)

$(OUT_PDF): $(SRC_TEX)
	$(LATEXMK) -$(XELATEX) -interaction=nonstopmode -halt-on-error -file-line-error $(SRC_TEX)

png: $(OUT_PNG)

# Convert PDF -> PNG with common tool fallbacks.
# Ensures opaque white background to keep the edge-label readable.
$(OUT_PNG): $(OUT_PDF)
	@if command -v magick >/dev/null 2>&1; then \
	  echo "[convert] magick -> $@"; \
	  magick -density $(DPI) $(OUT_PDF) -background white -alpha remove -alpha off -quality 100 $@; \
	elif command -v convert >/dev/null 2>&1; then \
	  echo "[convert] ImageMagick convert -> $@"; \
	  convert -density $(DPI) $(OUT_PDF) -background white -alpha remove -alpha off -quality 100 $@; \
	elif command -v pdftocairo >/dev/null 2>&1; then \
	  echo "[convert] pdftocairo -> $@"; \
	  pdftocairo -png -singlefile -r $(DPI) $(OUT_PDF) $(OUT_BASE); \
	elif command -v pdftoppm >/dev/null 2>&1; then \
	  echo "[convert] pdftoppm -> $@"; \
	  pdftoppm -png -singlefile -r $(DPI) $(OUT_PDF) $(OUT_BASE); \
	else \
	  echo "No PDF->PNG converter found. Install ImageMagick (magick/convert) or poppler (pdftocairo/pdftoppm)."; \
	  exit 1; \
	fi

clean:
	$(LATEXMK) -c
	@rm -f $(OUT_BASE).xdv $(OUT_BASE).synctex.gz

distclean: clean
	@rm -f $(OUT_PDF) $(OUT_PNG)

