VENV=.venv/bin/activate

PYTHON=$(shell which python3.8 python3.7 python3.6 python3 python | head -n1)
ifeq (, $(PYTHON))
$(error "No python{3,} in $(PATH)")
endif

up:
	docker-compose up -d --remove-orphans

logs:
	-docker-compose logs -f --tail=1000 -t

start stop ps down pull build top:
	docker-compose $@

dep: $(VENV)
	. $(VENV) && pip install wheel
	. $(VENV) && pip install -r requirements.txt

dev: $(VENV)
	. $(VENV) && pip install wheel
	. $(VENV) && pip install -r requirements-dev.txt

$(VENV):
	$(PYTHON) -m venv .venv

clean:
	rm -rf .venv __pycache__ .mypy_cache
	find . -iname \*.pyc -exec rm -v \;

.PHONY:	dev dep init start stop ps down pull build top logs up clean
