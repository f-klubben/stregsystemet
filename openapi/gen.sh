OUT=${1:-$PWD/out}
docker run --rm -v $(pwd):/local -v $OUT:/out redocly/cli build-docs /local/stregsystem.yaml -o /out/index.html
