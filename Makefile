all:
	cd test;$(MAKE)
	cd examples;$(MAKE)
	cd gallery;$(MAKE)
	cd manual;$(MAKE)
	cd faq;$(MAKE)
	cd www/png;$(MAKE)
	cd www;$(MAKE)

clean:
	cd examples;$(MAKE) clean
	cd gallery;$(MAKE) clean
	cd manual;$(MAKE) clean
	cd faq;$(MAKE) clean
	cd www/png;$(MAKE) clean
	cd www;$(MAKE) clean
