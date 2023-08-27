(function(){

    var pcastPlayers = document.querySelectorAll('.audio-player');
    
    for(i=0;i<pcastPlayers.length;i++) {
      var player = pcastPlayers[i];
      var audio = player.querySelector('audio');
      var play = player.querySelector('.player-play');
      var pause = player.querySelector('.player-pause');
      var rewind = player.querySelector('.player-backward');
      var forward = player.querySelector('.player-forward');
      var progress = player.querySelector('.player-progress');
      var currentTime = player.querySelector('.player-currenttime');
      var duration = player.querySelector('.player-duration');
        
      pause.style.display = 'none';
      
      var toHHMMSS = function ( totalsecs ) {
          var sec_num = parseInt(totalsecs, 10);
          var hours   = Math.floor(sec_num / 3600);
          var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
          var seconds = sec_num - (hours * 3600) - (minutes * 60);
  
          if (hours   < 10) {hours   = "0"+hours; }
          if (minutes < 10) {minutes = "0"+minutes;}
          if (seconds < 10) {seconds = "0"+seconds;}
          
          var time = hours+':'+minutes+':'+seconds;
          return time;
      }
      
      audio.addEventListener('loadedmetadata', function(){
        progress.setAttribute('max', Math.floor(audio.duration));
        duration.textContent  = toHHMMSS(audio.duration);
      });
      
      audio.addEventListener('timeupdate', function(){
        progress.setAttribute('value', audio.currentTime);
        currentTime.textContent  = toHHMMSS(audio.currentTime);
      });

      audio.addEventListener('play', function(){
        play.style.display = 'none';
        pause.style.display = 'inline-block';
      });
      
      play.addEventListener('click', function(){
        this.style.display = 'none';
        pause.style.display = 'inline-block';
        pause.focus();
        audio.play();
      }, false);
  
      pause.addEventListener('click', function(){
        this.style.display = 'none';
        play.style.display = 'inline-block';
        play.focus();
        audio.pause();
      }, false);
   
      rewind.addEventListener('click', function(){
        audio.currentTime -= 15;
      }, false);

      forward.addEventListener('click', function(){
        audio.currentTime += 15;
      }, false);
      
      progress.addEventListener('click', function(e){
        audio.currentTime = Math.floor(audio.duration) * (e.offsetX / e.target.offsetWidth);
      }, false);
  
    }
  })(this);