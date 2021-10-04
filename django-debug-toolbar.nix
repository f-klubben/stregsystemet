{ pkgs ? import <nixpkgs> {}
, pythonPackages ? pkgs.python39Packages
}:
pythonPackages.buildPythonPackage rec {
  pname = "django-debug-toolbar";
  version = "1.11.1";

  src = pythonPackages.fetchPypi {
    inherit version pname;
    sha256 = "0n4i1zpfxd7y0gnc4i25wki84822nr85hbmh0fw39bbzr5cyzx8h";
  };

  propagatedBuildInputs = [
    pythonPackages.django_2
  ];

  doCheck = false;

  meta = with pkgs.lib; {
    description = "A configurable set of panels that display various debug information about the current request/response.";
    homepage = "https://github.com/jazzband/django-debug-toolbar";
    license = licenses.bsd3;
  };
}
