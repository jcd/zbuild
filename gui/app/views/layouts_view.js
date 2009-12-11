/*globals $ document W App */
"use strict";

App.Views.Layouts = W.View.create({
	
	chrome: function () {
		// contentBox
		var headerBox = W.Widgets.Box.build({classes: "headerBox"});
		App.page().append(headerBox);

		// Name label
		var nameLabel = W.Widgets.Label.build({content: "ZBuild", classes: "logoText"});

		headerBox.append(nameLabel);

		headerBox.append(W.Widgets.Link.build({content: 'New build', classes: 'menuActions', 
				click: App.Controllers.Build.createNew}));

		headerBox.append(W.Widgets.Link.build({content: 'Monitor', classes: 'menuActions', 
				click: App.Controllers.Build.createNew}));

		headerBox.append(W.Widgets.Link.build({content: 'Configure', classes: 'menuActions', 
				click: App.Controllers.Build.createNew}));

		var contentBox = W.Widgets.Box.build({classes: "contentBox"});
		contentBox.attr('id',"content");
		App.page().append(contentBox);

	},
	

});