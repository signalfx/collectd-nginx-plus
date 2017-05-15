default: clean package

.PHONY: clean
clean:
	rm -rf .tox
	rm -rf nosetests.xml
	rm -rf pylint.out

.PHONY: test
test:
	tox -e nose || true

.PHONY: check
check:
	tox -e pylint || true
