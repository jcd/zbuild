/*globals $ document W App */
"use strict";

App.Models.Stage = W.Model.create({

	all: function(callback) {
	    jQuery.getJSON(App.server + "/stage", callback);
	},

	get: function(id, callback) {
	    jQuery.getJSON(App.server + "/stage/"+id, callback);
	}

});