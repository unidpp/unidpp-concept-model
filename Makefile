SRC := $(wildcard views/*.lutaml)
PNG := $(patsubst views/%.lutaml,images/%.png,$(SRC))

all: $(PNG)

images/%.png: views/%.lutaml | images
	bundle exec lutaml lml generate -t png -o $@ $<

images:
	mkdir images

# Rendering is the validation: a view that generates is a view that
# parses and lays out (lutaml 0.10 has no standalone lint).
validate: $(PNG)
	@echo "every view renders"

clean:
	rm -f images/*.png

.PHONY: all validate clean
