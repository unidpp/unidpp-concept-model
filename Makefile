SRC := $(wildcard views/*.lutaml)
PNG := $(patsubst views/%.lutaml,images/%.png,$(SRC))

all: $(PNG)

images/%.png: views/%.lutaml | images
	bundle exec lutaml lml generate -t png -o $@ $<

images:
	mkdir images

validate:
	@for f in views/*.lutaml; do bundle exec lutaml lml lint $$f || exit 1; done
	@echo "views lint clean"

clean:
	rm -f images/*.png

.PHONY: all validate clean
