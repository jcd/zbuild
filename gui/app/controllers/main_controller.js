/*globals $ document W App */
"use strict";

App.Controllers.Main = W.Controller.create({
	
	// The load method is called to start the application
	init: function () {
		// Draw the general main layout
	    tabs = [ { content : 'New build', click: App.Controllers.Build.createNew, selected: 1 },
                     { content : 'Monitor' },
                     { content : 'Fisk' } ] 
	    $('#page').render('layout', { tabsl: tabs } )
	}
	
});