var hitmarker = function() {
    this.marker = new Image(48, 48)
    this.marker.src = hitmarkerimage
    this.marker.style.position = 'absolute'
    this.marker.style.display = 'none'
    this.clack = document.createElement('audio')
    this.clack.src = hitmarkersound;
    this.init()
}

hitmarker.prototype.init = function() {
    var self = this
    document.body.appendChild(self.marker)
    console.log(self.marker)
    document.addEventListener('input', function(e) {
        var r = Math.random,
            n=0,
            d=document,
            w=window;
        self.marker.style.top = w.innerHeight * (r() * (0.4) + 0.1) + 'px'
        self.marker.style.left = w.innerWidth * (r() * (0.5) + 0.2) + 'px'
        self.marker.style.display = 'block'
        self.clack.play()
        window.setTimeout(function() {
            self.marker.style.display = 'none'
        }, 1000)
    })

}

new hitmarker()
