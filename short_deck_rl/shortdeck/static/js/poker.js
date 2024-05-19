document.addEventListener('DOMContentLoaded', function() {
    // animation for regular raise or call by the player
    function animatePlayerChipsToCenter(betAmount) {
        const playerChips = document.getElementById('movingChipsPlayer');
        
        // Create and style the bet amount
        const betAmountText = document.createElement('div');
        betAmountText.textContent = `+$20`;
        betAmountText.classList.add('bet-amount-text');

        // Position the bet amount
        betAmountText.style.position = 'absolute';
        betAmountText.style.left = '27%'; 
        betAmountText.style.top = '45%'; 
        betAmountText.style.transform = 'translate(-50%, -50%)';
        betAmountText.style.zIndex = 100; 
        document.body.appendChild(betAmountText);
    
        // Fade in and flash the bet amount
        gsap.fromTo(betAmountText, 
            { autoAlpha: 0 }, 
            { 
                duration: 0.5, 
                autoAlpha: 1, 
                repeat: 3, 
                yoyo: true,
                onComplete: () => {
                    gsap.to(betAmountText, {
                        duration: 1, 
                        autoAlpha: 0, 
                        delay: 1, 
                        onComplete: () => betAmountText.remove() 
                    });
                }
            }
        );
        // Animation of chips towards the pot
        gsap.set(playerChips, { display: 'block' });
        gsap.to(playerChips, {
            duration: 2,
            left: '15%', 
            top: '70%', 
            x: '-50%', 
            y: '-50%',
            onComplete: () => {
                playerChips.style.display = 'none'; 
            }
        });
    }
    // animation for re-raise by the player, so raising to 40
    function animatePlayerChipsToCenter40() {
        const playerChips = document.getElementById('movingChipsPlayer40');

        // Create and style the bet amount
        const betAmountText = document.createElement('div');
        betAmountText.textContent = `+$40`;
        betAmountText.classList.add('bet-amount-text');

        // Position the bet amount
        betAmountText.style.position = 'absolute';
        betAmountText.style.left = '27%'; 
        betAmountText.style.top = '45%'; 
        betAmountText.style.transform = 'translate(-50%, -50%)';
        betAmountText.style.zIndex = 100; 
        document.body.appendChild(betAmountText);

        // Fade in and flash the bet amount 
        gsap.fromTo(betAmountText, 
            { autoAlpha: 0 }, 
            { 
                duration: 0.5, 
                autoAlpha: 1, 
                repeat: 3, 
                yoyo: true,
                onComplete: () => {
                    gsap.to(betAmountText, {
                        duration: 1, 
                        autoAlpha: 0, 
                        delay: 1, 
                        onComplete: () => betAmountText.remove() 
                    });
                }
            }
        );

        // Animation of chips towards the pot
        gsap.set(playerChips, { display: 'block' });
        gsap.to(playerChips, {
            duration: 2,
            left: '15%',  
            top: '70%',  
            x: '-50%', 
            y: '-50%',
            onComplete: () => {
                playerChips.style.display = 'none'; 
            }
        });
        }

    // animation for regular raise or call by the AI
    function animateAIChipsToCenter() {
        const aiChips = document.getElementById('movingChipsAI');
        // Create and style the bet amount 
        const betAmountText = document.createElement('div');
        betAmountText.textContent = `+$20`;
        betAmountText.classList.add('bet-amount-text');
        // Position the bet amount
        betAmountText.style.position = 'absolute';
        betAmountText.style.left = '27%'; 
        betAmountText.style.top = '35%'; 
        betAmountText.style.transform = 'translate(-50%, -50%)';
        betAmountText.style.zIndex = 100; 
        document.body.appendChild(betAmountText);

        // Fade in and flash the bet amount
        gsap.fromTo(betAmountText, 
            { autoAlpha: 0 }, 
            { 
                duration: 0.5, 
                autoAlpha: 1, 
                repeat: 3, 
                yoyo: true,
                onComplete: () => {
                    gsap.to(betAmountText, {
                        duration: 1, 
                        autoAlpha: 0, 
                        delay: 1, 
                        onComplete: () => betAmountText.remove()
                    });
                }
            }
        );
        // Animation of chips towards the pot from the AI's hand
        gsap.set(aiChips, { x: 10, y: 10, display: 'block' });
        gsap.to(aiChips, {
            duration: 2,
            left: '20%',  
            top: '50%',  
            x: '-50%', 
            y: '-50%', 

            onComplete: () => {
                gsap.set(aiChips, { display: 'none' }); 
            }
        });
    }
    
    // animation for re-raise by the AI, so raising to 40
    function animateAIChipsToCenter40() {
        const aiChips = document.getElementById('movingChipsAI40');

        const betAmountText = document.createElement('div');
        betAmountText.textContent = `+$40`;
        betAmountText.classList.add('bet-amount-text');

        // Position the bet amount 
        betAmountText.style.position = 'absolute';
        betAmountText.style.left = '27%'; 
        betAmountText.style.top = '35%'; 
        betAmountText.style.transform = 'translate(-50%, -50%)';
        betAmountText.style.zIndex = 100; 
        document.body.appendChild(betAmountText);

        // Fade in and flash the bet amount 
        gsap.fromTo(betAmountText, 
            { autoAlpha: 0 }, 
            { 
                duration: 0.5, 
                autoAlpha: 1, 
                repeat: 3, 
                yoyo: true,
                onComplete: () => {
                    gsap.to(betAmountText, {
                        duration: 1,
                        autoAlpha: 0, 
                        delay: 1, 
                        onComplete: () => betAmountText.remove() 
                    });
                }
            }
        );

        // Animation of chips towards the pot from the AI's ahnd
        gsap.set(aiChips, { x: 10, y: 10, display: 'block' });
        gsap.to(aiChips, {
            duration: 2,
            left: '20%',  
            top: '50%',  
            x: '-50%', 
            y: '-50%', 

            onComplete: () => {
                gsap.set(aiChips, { display: 'none' });
            }
        });
    }

// Used to trigger the chip animations depending on what the previous action was.
  document.getElementById('actionForm').addEventListener('submit', function(event) {
    const actionValue = event.submitter.value;

    // Check the last action made by the AI
    const lastActionText = document.getElementById('last_action').textContent.trim();
    const aiRaised = lastActionText.includes('AI raises');

    // If the AI raised last and now the player is raising, raise value is 40
    if (actionValue === 'Raise' && aiRaised) {
        sessionStorage.setItem('playerRaised', 'true');
        updatePotValue();
        animatePlayerChipsToCenter40();
    } 
    // use the default animation, whne it's a regualr call or raise
    else if (actionValue === 'Call' || actionValue === 'Raise') {
        if (actionValue === 'Raise'){
            sessionStorage.setItem('playerRaised', 'true');
        }
        animatePlayerChipsToCenter();
        updatePotValue();
    }
    // If action is not Raise, playerRaised is cleared
    if (actionValue !== 'Raise') {
        sessionStorage.setItem('playerRaised', 'false');
    }

});
    // Use last action in log to animate AI's chips
    const lastAction = document.getElementById('last_action').textContent.trim();
    const playerRaised = sessionStorage.getItem('playerRaised') === 'true';
    if (playerRaised && lastAction.includes('AI raises')) {
        animateAIChipsToCenter40();
        updatePotValue();
    }
    else if (lastAction.includes('AI calls') || lastAction.includes('AI raises')) {
        animateAIChipsToCenter();
        updatePotValue();
    }
    });

// Logs the AI's last action and displays it beside the AI for 2 seconds
document.addEventListener('DOMContentLoaded', (event) => {
  const actionLogItem = document.querySelector('.actionLogItem');
  if (actionLogItem) {
      setTimeout(() => {
          actionLogItem.style.opacity = '0';
          setTimeout(() => {
              actionLogItem.remove(); 
          }, 0);
      }, 2000);
  }
});

// Used to show the AI folding by throwing the cards into the centre of the tbale
document.addEventListener('DOMContentLoaded', (event) => {
  const lastActionText = document.querySelector('#last_action').textContent.trim();

  // Check if last action indicates AI fold
  if (lastActionText === 'AI folds') {
      animateAIFold();
  }
  // aniimation for the cards being thrown
  function animateAIFold() {
      const aiCards = document.querySelectorAll('#botCards .cards');
      
      aiCards.forEach(card => {
          card.classList.add('thrownAI');

          // Listen for the end of the animation and then remove the cards
          card.addEventListener('animationend', () => {
              card.remove();
          });
      });
  }
});

// This is used to trigger and display the AI processing robot Gif
document.addEventListener('DOMContentLoaded', function() {
    const aiGif = document.getElementById('aiGif');
    const aiGifImage = aiGif.querySelector('img'); 
    const aiGifText = aiGif.querySelector('p'); 

    const actionForm = document.getElementById('actionForm');

    actionForm.addEventListener('submit', function(event) {
        const actionValue = event.submitter.value; 

        // Check if the action requires AI to make a decision, triggered by the players actions using the action form 
        if (actionValue === 'Call' || actionValue === 'Check' || actionValue === 'Raise') {
            // Show the AI GIF and text indicating AI is deciding
            aiGif.style.display = 'block';
            aiGifImage.style.display = 'block'; 
            aiGifText.style.display = 'block'; 

            // Hide the AI GIF after 4.5 seconds
            setTimeout(() => {
                aiGif.style.display = 'none';
                aiGifImage.style.display = 'none'; 
                aiGifText.style.display = 'none'; 
            }, 4500); 
        }
    });
});

// Used to show the PLayer folding by throwing the cards into the centre of the tbale, triggered by clicking the fold button
document.addEventListener('DOMContentLoaded', () => {
    const foldButton = document.querySelector('button[value="Fold"]');
    if (foldButton) {
        foldButton.addEventListener('click', (e) => {

            // Trigger the animation for folding cards
            const playerCards = document.querySelectorAll('#playerCards .cards');
            playerCards.forEach(card => {
                card.classList.add('thrown');
            });
            // 3 second animation 
            setTimeout(() => {
            }, 3000); 
        });
    }
});

// Next round loading bubble animation, when next round is clicked show laoading bubble
$(function() {
    $('#actionForm').submit(function(e) {
        var choice = $(this).find('button:focus').val();
        if (choice === 'Next Hand') {
            e.preventDefault();
            $('#loadingBubble').show();
            $('#loadingBubble').fadeOut(5000); 
            setTimeout(() => {
                this.submit();
            }, 0);
        }
    });
});

// retrieve pot value
function updatePotValue() {
    fetch(`/get_pot/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('pot').textContent = `Pot: $${data.pot}`;
        })
        .catch(error => console.error('Error fetching pot value:', error));
}
