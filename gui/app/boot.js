/*globals $ document W */
"use strict";

// Instantiate the App object and require the application sources
var App = W.App.create();

App.Models.require('stage');
App.Controllers.require('main', 'build');
App.Views.require('newbuild', 'layout');

W.ready(function () {
	App.init(function () {
		App.server = "";
		App.Controllers.Main.init();
	});
});
