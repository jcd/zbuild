/*globals $ document W App */
"use strict";

App.Controllers.Build = W.Controller.create({

	init: function() {
	    
	},

	createNew: function() {

	    var formatRows = function(e) {
		r = [];

		$.each(e.packages, function () {
			i = this.id;
 			r.push([ "<input value='" + i + "' type='hidden'><div class='packageName'>" + this.name + "</div>", 
				 "<input name='last_version_" + i + "' type='text' value='" + this.last_version + "' width='5' />", 
				 "<input name='last_revision_" + i + "'type='text' value='" + this.last_revision + "' width='5' />", 
				 "<input name='last_branch_" + i + "'type='text' value='" + this.last_branch + "' width='5' />", 
				 "<input name='build_" + i + "'type='checkbox' checked=checked width='5' />"
				 ]);
		    });
		return r;
	    }

	    $('#content').render('newbuild', { contr: App.Controllers.Build });
	    var sel = $('#stageSelect');

	    tableBind = W.UI.Table.bind(App.Models.Stage, $('#packagesList'), formatRows);
	    W.UI.Select.bind(App.Models.Stage, sel, undefined, tableBind);
	},
	
	onNewBuild: function(e) {
	    // New build has been ordered. 
	    // Now we need to look at all the packages needed and extract their versions
	    // in order to tell the backend to initiate a new build with the given
	    // packages and their respective versions/branch/tag/revision

	    rows = $('#packagesList').find('tr')
	    rows.splice(0,1);

	    var getInput = function(elm, name, id) {
		return $(elm).find('input[name="' + name + "_" + id + '"]')[0].value;
	    }
	    build_packs = []
	    $.each(rows, function() {

		    _id = $(this).find('input[type="hidden"]')[0].value;
		    _version = getInput(this, "last_version", _id);
		    _revision = getInput(this, "last_revision", _id);
		    _branch = getInput(this, "last_branch", _id);
		    _build = getInput(this, "build", _id);
		    
		    build_packs.push( { id : _id, version: _version, revision: _revision,
				branch: _branch, build: _build });
		});
	    
	    stage_id = 42;

	    buildOrder = { stage: stage_id, packages: build_packs };
	}

});