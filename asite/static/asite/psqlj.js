/* asite psqlj javascript */

// STARTUP

$(document).ready(function() {

	// focus the add form when its shown
	$('#addmodal').on('shown.bs.modal', function() {
		addformFocus();
		});
	
	// ensure that keypress listener on the final amount input
	$('#addform').on('focus', '.amount-input:last', function() {
		addformLastAmountBindKey();
	});

});

// set the add-new-row-on-keypress handler on the add form's
function addformLastAmountBindKey() {
	$('.amount-input').off('keypress');
	$('.amount-input:last').keypress(addformAddPosting);
}

// prepare the addform: ...
function addformFocus() {
}

// insert another posting row in the add form
function addformAddPosting() {
	if (!$('#addform').is(':visible')) {
		return;
	}
	// clone the old last-row to make a new last-row
	$('#addform .account-postings').append(
		$('#addform .account-group:last').clone().addClass('added-row')
	);
	// renumber and clear the new last account and amount fields
	var n = $('#addform .account-group').length;
	$('.account-input:last').prop('placeholder', 'Account '+n).val('');
	$('.amount-input:last').prop('placeholder', 'Amount '+n).val('');
	// move the keypress handler to the new last amount field
	addformLastAmountBindKey();
}


