.PHONY: all png svg clean distclean

# Build all *.typ in this directory to PNG (default) or SVG.
#   make            # build PNGs
#   make svg        # build SVGs alongside PNGs
#   make distclean  # remove generated PNG/SVG

SRCS := $(wildcard *.typ)
PNGS := $(SRCS:.typ=.png)
SVGS := $(SRCS:.typ=.svg)

PPI ?= 300
TYPST ?= typst

all: png

png: $(PNGS)

svg: $(SVGS)

%.png: %.typ
	$(TYPST) compile --ppi $(PPI) $< $@

%.svg: %.typ
	$(TYPST) compile --format svg $< $@

clean:
	@:

distclean:
	@rm -f $(PNGS) $(SVGS)
