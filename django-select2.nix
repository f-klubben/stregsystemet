{ pkgs ? import <nixpkgs> {}
, pythonPackages ? pkgs.python39Packages
}:
pythonPackages.buildPythonPackage rec {
  pname = "django-select2";
  version = "5.11.1";

  src = pkgs.fetchFromGitHub {
    owner = "codingjoe";
    repo = "django-select2";
    rev = version;
    sha256 = "0qsyliarbz1lc4pwrvcpp5lg6cfl4c7fipdbhjf7wyp7scradmxq";
  };

  propagatedBuildInputs = [
    pythonPackages.django_appconf
  ];

  doCheck = false;

  meta = with pkgs.lib; {
    description = "Select2 option fields for Django";
    homepage = "https://github.com/codingjoe/django-select2";
    license = licenses.mit;
  };
}
