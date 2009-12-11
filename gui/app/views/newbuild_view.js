/*globals $ document W App */
"use strict";

App.Views.Newbuild = W.View.create({

	build: function(select_cb) {

	    $('#content').html( tmpl("newbuild_tmpl",{}) );

	    var select = W.Widgets.Select.build({ size: 15, change: select_cb, id: 'stageSelect' });

	    $('#stageSelectDiv').html(select);

	}

});
