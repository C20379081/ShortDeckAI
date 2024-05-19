// JS for the modal which pops up when an action is selected, it displays the relevant information
$(document).ready(function() {
    $('button[data-action-id]').on('click', function() {
        var actionId = $(this).data('action-id');

        $.ajax({
            url: '/decision-data/' + actionId + '/',
            type: 'GET',
            success: function(data) {
                var cardImagesHtml = data.card_images.map(function(url) {
                    return '<img src="' + url + '" alt="Card" class="card-img">';
                }).join('');

                var modalBody = $('#actionInfoModal-' + actionId + ' .modal-body');
                modalBody.empty(); 

                // Append the basic info needed for the modal
                modalBody.append(`<br>${cardImagesHtml}<br>`);
                modalBody.append(`<br><strong>Action Taken:</strong> ${data.action_taken}<br>`);
                modalBody.append(`<strong>Actions Probability Distribution:</strong> ${JSON.stringify(data.probabilities)}`);
                modalBody.append(`<br><strong><Probability Explanation: </strong> ${data.explanatory_message}`); 

                // if pre flop display the hand vlaue and grid
                if(data.is_preflop) {
                    modalBody.append(`<br><strong>Hand Value:</strong> ${data.bucket_value}<br>`);
                    modalBody.append(`<br><div>${data.grid_html}</div>`);
                } 
                // post flop display what value the card and community cards up tot hat point are and display them
                else {
                    modalBody.append(`<br><strong>Hand Value:</strong> ${data.hand_type}`);

                    if(data.pair_category) {
                        modalBody.append(`<br> ${data.pair_category}<br><br>`);
                    }
                    var involvedCardsHtml = data.involved_cards_image.map(function(url) {
                        return '<img src="' + url + '" alt="Card" class="involved-card-img">';
                    }).join(' ');
                    modalBody.append(` ${involvedCardsHtml}`);
                }

                // Display legend
                if(data.colour_legend) {
                    var legendHtml = Object.entries(data.colour_legend).map(([colour, description]) => 
                        `<div class="legend-item">
                            <span class="colour-box" style="background-colour: ${colour};"></span>
                            <span class="colour-description">${description}</span>
                        </div>`).join('');
                    modalBody.append(legendHtml);
                }

                // Show the modal
                $('#actionInfoModal-' + actionId).modal('show');
            },
            error: function() {
                alert('Error fetching decision data.');
            }
        });
    });
});
