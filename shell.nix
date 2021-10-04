{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.buildEnv {
    name = "stregsystemEnv";
    paths = [
      (pkgs.python36.withPackages (
        ps: with ps; let
          djangoSelect2 = ps.buildPythonPackage rec {
            pname = "django-select2";
            version = "5.11.1";

            src = pkgs.fetchFromGitHub {
              owner = "codingjoe";
              repo = "django-select2";
              rev = version;
              sha256 = "0qsyliarbz1lc4pwrvcpp5lg6cfl4c7fipdbhjf7wyp7scradmxq";
            };

            propagatedBuildInputs = [
              ps.django_appconf
            ];

            doCheck = false;

            meta = with pkgs.lib; {
              description = "Select2 option fields for Django";
              homepage = "https://github.com/codingjoe/django-select2";
              license = licenses.mit;
            };
          };
          djangoDebugToolbar = ps.buildPythonPackage rec {
            pname = "django-debug-toolbar";
            version = "1.11.1";

            src = ps.fetchPypi {
              inherit version pname;
              sha256 = "0n4i1zpfxd7y0gnc4i25wki84822nr85hbmh0fw39bbzr5cyzx8h";
            };

            propagatedBuildInputs = [
              ps.django_2
            ];

            doCheck = false;

            meta = with pkgs.lib; {
              description = "A configurable set of panels that display various debug information about the current request/response.";
              homepage = "https://github.com/jazzband/django-debug-toolbar";
              license = licenses.bsd3;
            };
          };
        in [
          django_2 djangoSelect2 djangoDebugToolbar
        ]
      ))
    ];
  };
in
pkgs.mkShell {
  buildInputs = [
    pythonEnv
  ];
}
