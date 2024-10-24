function modifyCandle(date) {
   var dayOfMonth = date.getDate();

   dayOfMonth = Math.min(25, dayOfMonth);

   for (var i = 1; i < dayOfMonth; i++) {
      var dateLabel = document.getElementById("day_" + i);
      dateLabel.textContent = "";
   }

   var hour = new Date().getHours();
   var heightPerDay = 9;

   // Will not be continuous because of splitting the day into 48 pieces
   // instead of 24. I did so to show some of the current day on the candle
   // during the hours where the system is used
   var missingHeight = ((dayOfMonth - 1) * heightPerDay) + (10/48 * hour);
   var trunkInitialHeight = heightPerDay * 24 + 10;
   var newHeight = trunkInitialHeight - missingHeight;


   var trunk = document.getElementById("trunk");
   trunk.style.height = newHeight;

   // 74 is a constant from the SVG because inkscape places objects
   // weirdly. y = 0 in inkscape does not mean y = 0 in the svg...
   trunk.setAttribute('y', 74 + missingHeight);

   var topOfCandle = document.getElementById("top");

   topOfCandle.setAttribute('transform', "translate(0, " + missingHeight + ")");
}

setInterval(function(){
   modifyCandle(new Date());
}, 600000); //Runs every 10th minute
modifyCandle(new Date());
