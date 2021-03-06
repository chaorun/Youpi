/*****************************************************************************
 *
 * Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

function toggleDisplay(id) {
	var e = document.getElementById(id);
	if (!e) return;

	e.style.display == 'none' ? e.style.display = 'block' : e.style.display = 'none';
}

/*
 * Function: capitalizeHashKeys
 * Returns a copy of a hash with its keys's first letter capitalized
 *
 * Parameters:
 *  obj - object - hash
 *
 * Returns:
 *  Hash transformed
 *
 */
function capitalizeHashKeys(obj) {
	if (typeof obj != 'object')
		return null;

	obj = $H(obj);
	var tmp = new Hash();

	obj.keys().each(function(k) { 
		tmp.set(k.charAt(0).toUpperCase() + k.sub(/^./, ''), obj.get(k)); 
	});

	return tmp;
}

/*
 * Deletes all children nodes of a child
 *
 */
function removeAllChildrenNodes(node)
{
	if (!node) return;

	// Element ?
	if (node.nodeType != 1) {
		alert('Not an element. Cannot remove children');
		return;
	}

	if (node.hasChildNodes()) {
		for (var n=0; n < node.childNodes.length; n++) {
			node.removeChild(node.childNodes[n]);
		}
	}
}

// Can be used when .innerHTML does not work :(
function emptyContainer(container_id) {
	var container = document.getElementById(container_id);
	var p = container.parentNode;
	p.removeChild(container);
	var container = document.createElement('div');
	container.setAttribute('id', container_id);
	p.appendChild(container);

	return container;
}

/*
 * Reduces string length to max chars
 * Returns a span DOM element
 * '...' are added with a tooltip showing full text
 *
 */
function reduceString(msg, max) {
	var max = max ? max : 20;
	var span = document.createElement('span');
	var rmsg = msg;
	if (!msg) {
		span.appendChild(document.createTextNode('Unknown'));
		return span;
	}

	if (msg.length > max) {
		rmsg = msg.substr(0, max/2) + '...' + msg.substr(msg.length-(max-max/2+3), max-max/2+3);
		span.setAttribute('title', msg);
	}
	span.appendChild(document.createTextNode(rmsg));

	return span;
}

/*
 * Function: getSelect
 * Builds and returns a DOM select node
 *
 * with a supplied ID and a list of options as parameters
 *
 * Parameters:
 *  id - string: unique element id
 *  options - array of strings
 *  size - integer: > 1 for multiple select [default: 1]
 *  linenumber - boolean: activates line numbering [default: false]
 *
 * Returns:
 *  DOM select node
 *
 */
function getSelect(id, options, size, linenumber) {
	size = size ? size : 1;
	linenumber = typeof linenumber == 'boolean' ? linenumber : false;
	var select = new Element('select', {'id': id});
	if (size > 1) {
		select.setAttribute('size', size);
		select.setAttribute('multiple', 'true');
	}

	var opt = null;
	options.each(function(option, k) {
		opt = new Element('option', {value: option});
		linenumber ? opt.update("<span class=\"option_num\">" + (k+1) + '</span> ' + option) : opt.update(option);
		select.insert(opt);
	});

	if (size > 1) {
		// Select first option by default
		select.options[0].selected = true;
	}

	return select;
}

function getMessageNode(msg, cssClass, width, mtop) {
	var cls = cssClass || 'tip';
	var w = width || '40%';
	var t = mtop || '30px';

	var div = document.createElement('div');
	var p = document.createElement('p');

	div.setAttribute('class', cls);
	div.setAttribute('align', 'center');
	div.setAttribute('style', 'width: ' + w + '; margin-top: ' + t);
	p.appendChild(document.createTextNode(msg));
	div.appendChild(p);

	return div;
}

function getLoadingHTML(msg)
{
	return '<span><img src="/media/themes/' + guistyle + '/img/misc/snake-loader.gif"/> ' + msg + '...</span>';
}

/*
 * Returns a DOM table filled with json_results
 * json_results must look like {'header' : [], 'data' : []}
 *
 */
function getDOMTableFromResults(json_results, style)
{
	if (!json_results) return;

	// Default CSS style for table element
	var style = style || 'history';
	var res = json_results;

	// Table and header
	var table = document.createElement('table');
	var tr = document.createElement('tr');
	table.setAttribute('class', style);

	for (var j=0; j < res['header'].length; j++) {
		var th = document.createElement('th');
		th.appendChild(document.createTextNode(res['header'][j].capitalize()));
		tr.appendChild(th);
	}
	table.appendChild(tr);

	for (var i=0; i < res['data'].length; i++) {
		var tr = document.createElement('tr');

		for (var j=0; j < res['header'].length; j++) {
			var td = document.createElement('td');
			var data = res['data'][i][res['header'][j]];
			// Value's type
			var n;
			switch (data[1]) {
				case 'str':
					n =	data[0];
					break;
				case 'check':
					var n = document.createElement('img');
					var state = data[0] == 0 ? 'off' : 'on';
					n.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/checkbox_' + state + '.gif');
					break;
				case 'exit':
					var n = document.createElement('img');
					var state = data[0] == 0 ? 'success' : 'error';
					n.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_' + state + '.gif');
					break;
				case 'link':
					var n = document.createElement('a');
					n.setAttribute('href', data[2]);
					n.appendChild(document.createTextNode(data[0]));
					break;
				default:
					break;
			}
			td.insert(n);
			tr.appendChild(td);
		}

		table.appendChild(tr);
	}

	return table;
}

/*
 * ResultTable Object
 *
 * Usage:
 *
 * var t = new ResultTable();
 * container.appendChild(t.render(json));
 *
 * Serveur response must be a JSON object matching the following structure:
 *
 * json = { 'query'  : 'SQL query here',
 *			'fields' : 'Header fields',
 *			'hidden' : [list of hidden fields by name],
 *			'data'   : [[data1], [data2], ..., [datan]]
 * }
 *
 */
function ResultTable(style) {

	// Default CSS style for table element
	var style = style || 'history';
	
	this.render = function(json) {
		if (!json) {
			return document.createTextNode('Valid JSON response required !');
		}
	
		var resp = json;
	
		// Table and header
		var table = document.createElement('table');
		var tr = document.createElement('tr');
		table.setAttribute('class', style);
	
		for (var j=0; j < resp['fields'].length; j++) {
			var show = true;
			for (var k=0; k < resp['hidden'].length; k++) {
				if (resp['hidden'][k] == resp['fields'][j]) {
					show = false;
					break;
				}
			}
			
			// Hide if needed
			if (!show) continue;

			var th = document.createElement('th');
			th.appendChild(document.createTextNode(resp['fields'][j].capitalize()));
			tr.appendChild(th);
		}
		table.appendChild(tr);
	
		var rowClass;
		for (var i=0; i < resp['data'].length; i++) {
			var tr = document.createElement('tr');

			// Since i starts from 0 which is line #1
			i%2 == 0 ? rowClass = 'impair' : rowClass = 'pair';
			tr.setAttribute('class', rowClass);
	
			for (var j=0; j < resp['fields'].length; j++) {
				var show = true;
				for (var k=0; k < resp['hidden'].length; k++) {
					if (resp['hidden'][k] == resp['fields'][j]) {
						show = false;
						break;
					}
				}
				
				// Hide if needed
				if (!show) continue;

				var td = document.createElement('td');
				td.appendChild(document.createTextNode(resp['data'][i][j]));
				tr.appendChild(td);
			}
	
			table.appendChild(tr);
		}
	
		return table;
	}
}

/*
 * post_url: path to server-side script that MUST return a JSON object
 *           with those mandatory properties:
 *             json = {'data' : [list of json objects], 'header' : [list of header fields]}
 *
 */
function queryUrlDisplayAsTable(container_id, select_limit_id, post_url, style, handler)
{
	var container = document.getElementById(container_id);
	var sel = document.getElementById(select_limit_id);
	var handler = typeof handler == 'function' ? handler : null;
	var limit;

	sel ? limit = sel.options[sel.selectedIndex].value : limit = 0;

	var xhr = new HttpRequest(
		container.id,
		null, // Use default error handler
		// Custom handler for results
		function(resp) {
			if (resp.Error) {
				var d = new Element('div').addClassName('perm_not_granted').update(resp.Error);
				container.update(d);
				return;
			}
			container.update();
			container.insert(getDOMTableFromResults(resp, style));
			if (handler) handler(resp);
		}
	);

	post =	'limit=' + limit;

	// Send HTTP POST request
	xhr.send(post_url, post);
}

/*
 * Used in templates results.html and single_result.html
 *
 */
function results_showDetails(pname, id, fullpage) {
	var fullpage = fullpage ? true : false;
	var div = $('infopanel');
	var r = new HttpRequest(
		div.id,
		null,
		// Custom handler for results
		function(resp) {
			div.update();
			if (resp.Error) {
				var log = new Logger(div);
				log.msg_error('Processing results not available. An error occured.');
				currentReturnedData = false;
				return;
			}
			if (fullpage) {
				var a = new Element('a', {href: '/youpi/results/' + pname + '/' + id + '/', target: '_blank'});
				a.update("Click here to see a full page result for '" + resp.result.Title + "'");
				div.insert('[ ').insert(a).insert(' ]');
			}
			// Global variable
			currentReturnedData = resp.result;
			eval(pname + ".resultsShowEntryDetails('" + div.id + "')");
		}
	);

	var post = {
		Plugin: pname,
		Method: 'getTaskInfo',
		TaskId: id
	};
	r.send('/youpi/process/plugin/', $H(post).toQueryString());
}

/*
 * Common to every plugins. Call this function from your plugin plugin_XXX.js code
 * to add output directory support to your plugin.
 *
 */
function plugin_enableOutputDirectory(opts) {
	if (typeof opts != 'object')
		throw "Options must be an object";
	opts.default_path = opts.default_path || opts.outputdirs[0];

	var div = $(opts.container);
	p = new Element('p').setStyle({marginTop: '30px', fontSize: '12px', fontWeight: 'bold'});
	p.update('For convenience, you can change the directory suffix that will be used to save output data ');
	p.insert(new Element('u').update('for this cart item only')).insert(':').insert(new Element('br'));
	var d = new Element('div').setStyle({width: '60%', backgroundColor: 'lightgray', padding: '10px', marginTop: '10px'});
	var input = new Element('input', {id: 'output_path_input', type: 'text', size: '20', value: opts.random});
	var pathSel = new Element('select');
	opts.outputdirs.each(function(dir) {
		var opt = new Element('option', {value: dir}).update(dir);
		if (opts.default_path == dir)
			opt.writeAttribute('selected', 'selected');
		pathSel.insert(opt);
	});
	d.update(pathSel).insert(opts.suffix).insert(input).insert('/');
	p.insert(d);
	div.insert(p);

	var p = new Element('p').setStyle({marginTop: '30px', fontSize: '12px'});
	[[pathSel, 'change'], [input, 'keyup']].each(function(e) {
		e[0].observe(e[1], function() {
			p.select('tt')[0].update(pathSel.options[pathSel.selectedIndex].value + opts.suffix + input.value + '/');
		});
	});
	input.observe('keydown', function(e) {
		// Characters not allowed: ' ', '/', '\'
		if (e.keyCode == 32 || e.keyCode == 191 || e.keyCode == 220)
			e.stop();
	});

	p.update('All data produced will be stored into ').insert(
		new Element('tt', {id: 'output_target_path'}).setStyle({color: 'green'}).update(opts.default_path + opts.suffix + opts.random + '/')
	).insert('.');
	div.insert(p);
}

/*
 * Function: validate_container
 * Checks whether a container is valid.
 *
 * Parameters:
 *  container - string of DOM element for rendering content
 *
 * Returns:
 *  DOM element or null
 *
 */ 
function validate_container(container) {
	var d;
	if (typeof container == 'string' && container.length) {
		d = document.getElementById(container);
		if (!d) {
			_error("bad container '" + container + "' used!");
		return null;
		}
	}
	else if (typeof container == 'object') {
		d = container;
	}
else {
		_error('container must be string or a DOM object!');
		return null;
	}

	return d;
}

/*
 * Class: DropdownBox
 *
 * Dependencies:
 *  scriptaculous.js - 3rdParty Javascript library
 *
 * Constructor Parameters:
 *  container - DOM object or string: name of parent DOM block container
 *  title - string: box's title
 *
 */
function DropdownBox(container, title) 
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Top-level DOM container
	 *
	 */
	var _container = $(container);


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _title
	 * Box's title
	 *
	 */
	var _title;
	/*
	 * Var: _contentContainer
	 * Content DOM DIV container
	 *
	 */
	var _contentContainer;
	/*
	 * Var: _isTopLevelContainer
	 * true is the box is defined as a top level container (default: true)
	 *
	 */
	var _isTopLevelContainer = true;
	/*
	 * Var: _onClickHandler
	 * custom function handler to execute in response to onclick events on label
	 *
	 */
	var _onClickHandler = null;
	/*
	 * Var: _stateOpen
	 * true if the dropdown box is opened (default: false)
	 *
	 */
	var _stateOpen = false;
	/*
	 * Var: _titleNode
	 * DOM label node for box's title
	 *
	 */
	var _titleNode;
	/*
	 * Var: _mainDiv
	 * Main DIV (clickable) DOM node
	 *
	 */
	var _mainDiv;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
  	 * Function: _main
	 * Main entry point
	 *
	 */
	function _main() {
		_title = title;

		var topDiv = document.createElement('div');
		topDiv.setAttribute('class', 'ebox');
		_mainDiv = document.createElement('div');

		_mainDiv.observe('click', function() { 
			_toggleState();
			if (_onClickHandler)
				_onClickHandler();
		});

		_titleNode = new Element('label').insert(_title);
		var cdiv = new Element('div', {id: 'ddbox_' + Math.random() + '_content'}).hide();
		_contentContainer = cdiv;
		_mainDiv.insert(_titleNode);
		topDiv.insert(_mainDiv);
		topDiv.insert(cdiv);
		_container.insert(topDiv);

		_setOpen(false);
	}

	/*
  	 * Function: getRootNode
	 * Returns root (top-level) DOM node
	 *
	 * Returns:
	 *  Top-level DOM container
	 *
	 */
	this.getRootNode = function() {
		return _container;
	}

	/*
  	 * Function: setTitle
	 * Sets box's main title
	 *
	 */
	this.setTitle = function(title) {
		if (typeof title == 'string') {
			_title = title;
			_titleNode.innerHTML = '';
			_titleNode.appendChild(document.createTextNode(_title));
		}
		else
			alert('dbox::setTitle error: bad title, must be a string!');
	}

	/*
  	 * Function: getContentNode
	 * Returns content DOM node
	 *
	 * Returns:
	 *  Content DIV DOM container
	 *
	 */
	this.getContentNode = function() {
		return _contentContainer;
	}

	/*
  	 * Function: setTopLevelContainer
	 * Indicates whether the box is a top-level container
	 *
	 * CSS styles used depend on this parameter.
	 *
	 * Parameters:
	 *  is_top - boolean: True if top-level container
	 *
	 */
	this.setTopLevelContainer = function(is_top) {
		_isTopLevelContainer = (typeof is_top == 'boolean' && is_top) ? true : false;
		_setOpen(_stateOpen);
	}

	/*
  	 * Function: isTopLevelContainer
	 * Returns true if the box has been defined as a top level container 
	 *
	 * Returns:
	 *  boolean
	 *
	 */
	this.isTopLevelContainer = function() {
		return _isTopLevelContainer;
	}

	/*
  	 * Function: setOnClickHandler
	 * Defines custom handler function for OnClick box's events
	 *
	 * Parameters:
	 *  handler - function: custom handler function
	 *
	 */
	this.setOnClickHandler = function(handler) {
		_onClickHandler = typeof handler == 'function' ? handler : null;
	}

	/*
  	 * Function: getOnClickHandler
	 * Returns custom handler used
	 *
	 * Returns:
	 *  function handler or null
	 *
	 */
	this.getOnClickHandler = function() {
		return _onClickHandler;
	}

	/*
  	 * Function: isOpen
	 * Returns box's open state
	 *
	 * Returns:
	 *  boolean - true if open; otherwise false
	 *
	 */
	this.isOpen = function() {
		return _stateOpen;
	}

	/*
  	 * Function: setOpen
	 * Defines whether the box is open
	 *
	 * Parameters:
	 *  open - boolean
	 *
	 */
	this.setOpen = function(open) {
		_setOpen(open);
	}

	/*
  	 * Function: _toggleState
	 * Toggles box's state (opened or closed) 
	 *
	 */
	function _toggleState() {
		_stateOpen = !_stateOpen;
		_setOpen(_stateOpen);
	}

	/*
  	 * Function: _setOpen
	 * Defines whether the box is open
	 *
	 * Parameters:
	 *  open - boolean
	 *
	 */
	function _setOpen(open) {
		var gfx;
		_stateOpen = (typeof open == 'boolean' && open) ? true : false;
		_mainDiv.writeAttribute('class', 'banner_' + (_stateOpen ? 'opened' : 'closed') + (!_isTopLevelContainer ? '_child' : ''));
		_stateOpen ? $(_contentContainer).show() : $(_contentContainer).hide();
	}

	/*
  	 * Function: _main
	 * Main entry point
	 *
	 */
	_main();
}


/*
 * Class: Logger
 * Class providing logging facilities
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <Logger> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container - object or string: name of parent DOM block container
 *
 */
function Logger(container) 
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _log
	 * Top-level DOM container
	 *
	 */
	var _log;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _init
	 * Main entry point
	 *
	 */ 
	function _init() {
		if (typeof container == 'object') {
			_log = container;
		}
		else if (typeof container == 'string') {
			_log = document.getElementById(container);
		}
	
		if (!_log) {
			alert('logger error: no valid container defined!');
		}
	}

	/*
	 * Function: msg_status
	 * Display a status message
	 *
	 * Parameters:
	 *  msg - string: message
	 *
	 */ 
	this.msg_status = function(msg) {
		var line = new Element('div', {'class': 'logger_status'});
		line.insert(msg);
		_log.insert(line);
	}

	/*
	 * Function: insert
	 * Inserts any DOM element
	 *
	 * Parameters:
	 *  elem - DOM element
	 *
	 */ 
	this.insert = function(elem) {
		_log.insert(elem);
	}

	/*
	 * Function: clear
	 * Clear log
	 *
	 */ 
	this.clear = function() {
		_log.update();
	}

	/*
	 * Function: msg_ok
	 * Display an 'OK' message
	 *
	 * Parameters:
	 *  msg - string: message
	 *
	 */ 
	this.msg_ok = function(msg) {
		var line = new Element('div', {'class': 'logger_ok'});
		line.insert(msg);
		_log.insert(line);
	}

	/*
	 * Function: msg_warning
	 * Display a warning message
	 *
	 * Parameters:
	 *  msg - string: message
	 *
	 */ 
	this.msg_warning = function(msg) {
		var line = new Element('div', {'class': 'logger_warning'});
		line.insert(msg);
		_log.insert(line);
	}

	/*
	 * Function: msg_error
	 * Display an error message
	 *
	 * Parameters:
	 *  msg - string or DOM: message
	 *  alertBox - boolean: whether to display an alert box on the screen
	 *
	 */ 
	this.msg_error = function(msg, alertBox) {
		var do_ab = alertBox ? true : false;
		var line = new Element('div', {'class': 'logger_error'});
		line.insert(msg);
		_log.insert(line);
		if (do_ab)
			alert('Error: ' + msg);
	}

	_init();
}

/*
 * Function: getQueryString
 * Converts an object to a Hash then builds a QueryString
 *
 * Parameters:
 *  hash - object: object to convert
 *  strip - boolean: remove leading '&' if true. (default: true)
 *
 * Note:
 *  Unlike prototype's Hash#toQueryString(), this function does not convert special chars
 *  (useful for POST HTTP queries)
 *
 * Returns:
 *  query string - string
 *
 */ 
function getQueryString(hash, strip) {
	var strip = typeof strip == 'boolean' ? strip : true;
	if (typeof hash != 'object')
		console.error('hash must be an object!');

	var qs = '';
	var tmp = $H(hash).map(function(pair) {
		return '&' + pair.key + '=' + pair.value;
	}).each(function(entry) {
		qs += entry;
	})
	
	return (strip ? qs.sub(/&/, '') : qs);
}


/*
 * Namespace: Notifier
 * Provides some functions to notify user
 *
 */
var Notifier = {
	notify: function (msg, timeout) {
		Informer.info(msg);
	},
	/*
	 * Function: notify
	 * Static popup message. This is a native function, which can be used instead of the 
	 * 3rdParty Q lib.
	 *
	 * Parameters:
	 *  msg - string: message to display
	 *  timeout - float: time in seconds before message timeout
	 * 
	 */
	notify2: function (msg, timeout) {
		if (typeof msg != 'string')
			throw 'msg must be a string';

		if (timeout && typeof timeout != 'number')
			throw 'timeout must be a number';

		timeout = timeout ? timeout : this.defaultTimeout;
		timeout = timeout > 10 ? 10.0 : parseFloat(timeout);

		var d = $('notify_div');
		if (!d) {
			var d = new Element('div', {id: 'notify_div'}).addClassName('notify').hide();
			document.body.insert(d);
		}

		if (d.visible()) {
			// Busy, add to queue
			if (this.queue.length < this.max)
				this.queue.push(msg);
			return;
		}
		d.update(new Element('div').update(msg));
		d.appear({to: 0.8});
		d.fade({
			from: 0.8, 
			delay: timeout,
			afterFinish: function() {
				if (Notifier.queue.length)
					Notifier.notify(Notifier.queue.shift());
			}
		});
	},
	/*
	 * Var: defaultTimeout
	 * Default timeout in seconds
	 *
	 */
	defaultTimeout: 10.0,
	/*
	 * Var: queue
	 * Holds data awaiting to be processed (FIFO queue)
	 *
	 */
	queue: new Array(),
	/*
	 * Var: max
	 * Max elements in the queue
	 *
	 */
	max: 10
};

/*
 * Namespace: ResultsHelpers
 * Namespace for plugin helper functions (for the results page)
 * 
 */
var ResultsHelpers = {
	/*
	 * Function: getCondorJobLogsEntry
	 * Builds and return a TABLE DOM element with info related to Condor job ID and log files, when available
	 *
	 * Parameters:
	 *  clusterId - string: cluster Id
	 *  taskId - Task DB Id
	 *
	 * Returns:
	 *  TABLE DOM element
	 * 
	 */
	getCondorJobLogsEntry: function(clusterId, taskId) {
		var tab = new Element('table').setStyle({width: '100%'});
		var tr = new Element('tr');
		var td = new Element('td', {colspan: 2}).addClassName('qfits-result-header-title');
		td.insert('Condor Job Logs');
		tr.insert(td);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td', {colspan: 2});
		tr.insert(td);
		tab.insert(tr);
		var htab = new Element('table').setStyle({width: '100%'});
		td.insert(htab);
		tr = new Element('tr');
		td = new Element('td');
		td.insert('Cluster Id: ' + (clusterId == 'None' ? '--' : clusterId)).insert(new Element('br'));
		tr.insert(td);
		td = new Element('td');

		var msg = 'Log files: ';
		if (clusterId == 'None') {
			msg += '--';
		}
		else {
			var r = new HttpRequest(
				td,
				null, // Use default error handler
				// Custom handler for results
				function(resp) {
					td.update();
					var logs = $H(resp.logs);
					var tab = new Element('table');
					var ttr, ttd;
					logs.each(function(pair) {
						ttr = new Element('tr');
						ttd = new Element('td');
						ttd.insert('Condor ' + pair.key + ': ');
						ttr.insert(ttd);
						ttd = new Element('td');
						if (logs.get(pair.key).length) {
							var a = new Element('a', {target: '_blank'}).update(logs.get(pair.key));
							ttd.insert(a);
							ttr.insert(ttd);
							ttd = new Element('td').setStyle({textAlign: 'right'});
							ttd.insert(resp.sizes[pair.key]);
							ttr.insert(ttd);
						}
						else {
							ttd.setStyle({colspan: 2});
							ttd.insert('--');
							ttr.insert(ttd);
						}
						tab.insert(ttr);
					});
					td.insert(tab);
				}
			);

			var post = {
				Method: 'getCondorLogFilesLinks',
				TaskId: taskId
			};
			r.send('/youpi/cluster/logs/', $H(post).toQueryString());
		}

		td.insert(msg);
		tr.insert(td);
		htab.insert(tr);

		return tab;
	},
	/*
	 * Function: getPermissionsEntry
	 * Builds and return a TABLE DOM element with info related to user permissions
	 *
	 * Parameters:
	 *  taskId - Task DB Id
	 *
	 * Returns:
	 *  TABLE DOM element
	 * 
	 */
	getPermissionsEntry: function(taskId) {
		var tab = new Element('table').setStyle({width: '100%'});
		var tr = new Element('tr');
		var td = new Element('td', {colspan: 2}).addClassName('qfits-result-header-title');
		td.insert('User Permissions');
		tr.insert(td);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.update(get_permissions('task', taskId, function(resp, misc) {
			if (resp.currentUser.write) {
				var delb = new Element('img', {
					title: 'Click here to delete this processing',
					src: '/media/themes/' + guistyle + '/img/misc/delete.png'}
				).addClassName('clickable');
				delb.observe('click', function() {
					boxes.confirm('Are you sure you want to delete this processing from the database?<br/><br/>' + 
						"Please note that output data <b>will NOT be deleted</b> by the application. It's up to you to delete the " +
						"data in the output directory.", function() {
						var dr = new HttpRequest(
							null,
							null,
							function(r) {
								var log = new Logger(td);
								if (r.Error) {
									log.msg_error('Error: ' + r.Error + '. Data not deleted.');
									return;
								}
								if (r.success) {
									var row = $$('table.results')[0].select('tr[id=res_' + taskId + ']')[0].hide();
									$('infopanel').update();
									var log = new Logger($('infopanel'));
									log.msg_ok("Processing successfully deleted.");
								}
								else {
									log.msg_warning('Not enough permissions. Data not deleted.');
									boxes.perms_discard();
								}
							}
						);
						dr.send('/youpi/results/delete/', $H({TaskId: taskId}).toQueryString());
					});
				});
				var ddiv = $('task_perms_del_div');
				if (!ddiv) {
					ddiv = new Element('div', {id: 'task_perms_del_div'});
					ddiv.insert('You can ').insert(delb).insert(' this processing');
					td.insert(ddiv);
				}
				ddiv.show();
			}
			else {
				// No user write permission
				if ($('task_perms_del_div')) $('task_perms_del_div').hide();
			}
		}));
		tr.insert(td);
		tab.insert(tr);

		return tab;
	}
};

/*
 * Namespace: boxes
 * Namespace for custom boxes using the Modalbox capabilities
 * 
 */
var boxes = {
	/*
	 * Function: confirm
	 * Display a modern JS confirm box
	 *
	 * Parameters:
	 *  msg - string: message to display
	 *  onAcceptHandler - function: callback executed when the 'Ok' button is clicked
	 *  title - string: header title [optional]
	 * 
	 */
	confirm: function(msg, onAcceptHandler, title) {
		if (typeof msg != 'string')
			throw "msg must be a string";
		if (typeof onAcceptHandler != 'function')
			throw "onAcceptHandler must be a function";
		if (title && typeof title != 'string')
			throw "title must be a string";

		var title = title ? title : 'Confirm';
		var d = new Element('div').addClassName('modal_warning');
		var bd = new Element('div').setStyle({paddingTop: '10px', textAlign: 'right'});
		var yesButton = new Element('input', {id: 'modalbox_ok_input', type: 'button', value: 'Ok'}).setStyle({marginRight: '20px'});
		var noButton = new Element('input', {id: 'modalbox_cancel_input', type: 'button', value: 'Cancel'});
		bd.insert(yesButton).insert(noButton);
		d.update(msg);
		d.insert(bd);

		Modalbox.show(d, {
			title: title, 
			width: 300, 
			overlayClose: false,
			slideDownDuration: .25,
			slideUpDuration: .25,
			afterLoad: function() {
				$('modalbox_ok_input').observe('click', function() { 
					Modalbox.accept = true;
					Modalbox.hide(); 
				});
				$('modalbox_cancel_input').observe('click', function() { 
					Modalbox.accept = false;
					Modalbox.hide(); 
				});
			},
			afterHide: function() {
				if (Modalbox.accept && onAcceptHandler)
					onAcceptHandler();
			}
		});
	},
	/*
	 * Function: browsePath
	 * File/Path selector box
	 *
	 * Parameters:
	 *  onAcceptHandler - function: callback executed when the 'Ok' button is clicked
	 *  fileTypes - array: array of string patterns
	 *  title - string: header title [optional]
	 * 
	 */
	browsePath: function(filePatterns, onAcceptHandler, title) {
		if (typeof onAcceptHandler != 'function')
			throw "onAcceptHandler must be a function";
		if (typeof filePatterns != 'object')
			throw "fileTyeps must be an array of strings";
		if (title && typeof title != 'string')
			throw "title must be a string";

		var title = title ? title : 'Select a data path';
		var patd = new Element('div').setStyle({marginTop: '5px', marginBottom: '10px'}).update('File pattern:');
		var d = new Element('div').update(patd);
		var bd = new Element('div').setStyle({paddingTop: '10px', textAlign: 'right'});
		var yesButton = new Element('input', {id: 'modalbox_ok_input', type: 'button', value: 'Ok'}).setStyle({marginRight: '20px'});
		var noButton = new Element('input', {id: 'modalbox_cancel_input', type: 'button', value: 'Cancel'});
		bd.insert(yesButton).insert(noButton);

		var selectedPath = null;
		box_file_browser = new LightFileBrowser('box_file_browser');
		box_file_browser.setRootTitle(_fileBrowserSettings.rootTitle);
		box_file_browser.setFilteringPatterns(filePatterns);
		box_file_browser.setRootDataPath(_fileBrowserSettings.rootDataPath);
		box_file_browser.setTreeviewHeight('300px');
		box_file_browser.setBranchClickedHandler(function(path) {
			selectedPath = path;
		});

		var pati = new Element('input', {value: filePatterns.join(';'), title: 'Set file patterns separated by semi-colons'});
		pati.observe('change', function() {
			box_file_browser.setFilteringPatterns(this.value.split(';'));
		});
		patd.insert(pati);

		d.insert(box_file_browser.render());
		d.insert(bd);

		Window._accept = false;
		var win = new Window({
			className: 'alphacube',
			width: 400, 
			height: 370, 
			minimizable: false, 
			maximizable: false, 
			resizable: false, 
			draggable: false,
			title: title
		});
		win.getContent().update(d);
		win.setCloseCallback(function() {
			if (Window._accept && onAcceptHandler)
				onAcceptHandler(selectedPath, pati.value.split(';'));
			return true;
		});
		win.showCenter(true);

		$('modalbox_ok_input').observe('click', function() { 
			Window._accept = true;
			win.close(); 
		});

		$('modalbox_cancel_input').observe('click', function() { 
			win.close(); 
		});
	},
	/*
	 * Function: alert
	 * Display a modern JS aler box
	 *
	 * Parameters:
	 *  msg - string: message to display
	 *  title - string: header title [optional]
	 * 
	 */
	alert: function(msg, title) {
		if (typeof msg != 'string')
			throw "msg must be a string";
		if (title && typeof title != 'string')
			throw "title must be a string";

		var title = title ? title : 'Notification';
		var d = new Element('div').addClassName('modal_warning');
		var bd = new Element('div').setStyle({paddingTop: '10px', textAlign: 'right'});
		var okButton = new Element('input', {id: 'modalbox_ok_input', type: 'button', value: 'Ok'});
		bd.insert(okButton);
		d.update(msg);
		d.insert(bd);

		Modalbox.show(d, {
			title: title, 
			width: 300, 
			overlayClose: false,
			slideDownDuration: .25,
			slideUpDuration: .25,
			afterLoad: function() {
				$('modalbox_ok_input').observe('click', function() { 
					Modalbox.accept = true;
					Modalbox.hide(); 
				});
			}
		});
	},
	/*
	 * Function: perms_discard
	 * Alert box for users with bad permissions
	 * 
	 */
	perms_discard: function() {
		boxes.alert("Sorry, you don't have enough permissions to do it.");
	},
	/*
	 * Function: permissions
	 * Display a permissions box
	 *
	 * Parameters:
	 *  container_id - string: DOM container id
	 *  handler - function: custom handler function (can be null)
	 *  target - string: entity name
	 *  key - string: key used to find a match
	 *  perms - object: user permissions for this object
	 *  userInfo - object: additional information
	 *  misc - any: any data (passed to handler, if any) [optional]
	 *  title - string: title message [optional]
	 * 
	 * Notes:
	 *  The following format must be used:
	 *  
	 *  perms format: {user: {read: bool, write: bool}, group: {read: bool, write: bool}, others: {read: bool, write: bool}}
	 *  userInfo format: {username: <string>, groupname: <string>, groups: <array>}
	 *
	 */
	permissions: function(container_id, handler, target, key, perms, userInfo, misc, title) {
		if (typeof container_id != 'string')
			throw "container_id must be a string";
		if (typeof target != 'string' || typeof key != 'string')
			throw "Target and key must be strings";

		if (typeof perms != 'object' || typeof userInfo != 'object')
			throw "perms and userInfo must be objects";

		//
		var title = typeof title == 'string' ? title : 'User Permissions';
		var d = new Element('div');
		var bd = new Element('div').setStyle({paddingTop: '10px', textAlign: 'right'});
		var yesButton = new Element('input', {id: 'modalbox_ok_input', type: 'button', value: 'Apply'}).setStyle({marginRight: '20px'});
		var resetButton = new Element('input', {
			id: 'modalbox_reset_input', 
			title: 'Reset the form to your default permissions', 
			type: 'button', 
			value: 'Reset'
		}).setStyle({marginRight: '20px'});
		var noButton = new Element('input', {id: 'modalbox_cancel_input', type: 'button', value: 'Cancel'});
		bd.insert(yesButton).insert(resetButton).insert(noButton);

		function update_table(userInfo, perms) {
			var t = new Element('table').setStyle({width: '100%'});
			var tr, td, th;
			var r, w;

			// Header
			tr = new Element('tr').insert(new Element('th')).insert(new Element('th'));
			th = new Element('th').update('Read');
			tr.insert(th);
			th = new Element('th').update('Write');
			tr.insert(th);
			t.insert(tr);

			var chk;
			// Owner
			tr = new Element('tr');
			th = new Element('th').insert('Owner');
			tr.insert(th);
			td = new Element('td').insert(userInfo.username);
			tr.insert(td);
			td = new Element('td').insert(new Element('input', {type: 'checkbox', checked: 'checked', disabled: 'disabled'}));
			tr.insert(td);
			td = new Element('td');
			chk = new Element('input', {type: 'checkbox'});
			if (perms.user.write) chk.writeAttribute('checked', 'checked');
			td.insert(chk);
			tr.insert(td);
			t.insert(tr);

			// Group
			tr = new Element('tr');
			th = new Element('th').insert('Group');
			tr.insert(th);
			var gsel = getSelect('perm_group_select', userInfo.groups);
			gsel.select('option').each(function(opt) {
				if (opt.value == userInfo.groupname)
					opt.writeAttribute('selected', 'selected');
			});
			td = new Element('td').insert(gsel);
			tr.insert(td);

			td = new Element('td');
			chk = new Element('input', {type: 'checkbox'});
			if (perms.group.read) chk.writeAttribute('checked', 'checked');
			td.insert(chk);
			tr.insert(td);

			td = new Element('td');
			chk = new Element('input', {type: 'checkbox'});
			if (perms.group.write) chk.writeAttribute('checked', 'checked');
			td.insert(chk);
			tr.insert(td);
			t.insert(tr);

			// Others
			tr = new Element('tr');
			th = new Element('th').insert('Others');
			tr.insert(th);
			td = new Element('td').insert('All');
			tr.insert(td);

			td = new Element('td');
			chk = new Element('input', {type: 'checkbox'});
			if (perms.others.read) chk.writeAttribute('checked', 'checked');
			td.insert(chk);
			tr.insert(td);

			td = new Element('td');
			chk = new Element('input', {type: 'checkbox'});
			if (perms.others.write) chk.writeAttribute('checked', 'checked');
			td.insert(chk);
			tr.insert(td);
			t.insert(tr);

			return t;
		}

		d.insert('You can use this form to define permissions related to data access:<br/>');
		var tdiv = new Element('div', {id: 'modalbox_tab_div'});
		tdiv.update(update_table(userInfo, perms));
		d.insert(tdiv);
		d.insert(bd);

		Modalbox.validated = false;
		Modalbox.show(d, {
			title: title, 
			overlayClose: false,
			slideDownDuration: .25,
			slideUpDuration: .25,
			afterLoad: function() {
				$('modalbox_ok_input').observe('click', function() { 
					// Apply permissions
					checks = $('modalbox_tab_div').select('input[type=checkbox]');
					// Default mask fofr user/group/others r/w permissions
					vals = [1, 0, 0, 0, 0, 0];
					checks.each(function(chk, k) {
						if (chk.checked) vals[k] = 1;
					});
					var pr = new HttpRequest(
						null,
						null,
						function(r) {
							if (r.Error) return;
							// Notify permissions changes
							document.fire('permissions:updated', {
								container_id: container_id, // DOM container
								target: target, 
								key: key, 
								handler: handler,
								misc: misc
							});
							Modalbox.hide();
						}
					);

					var newgrp;
					$('perm_group_select').select('option').each(function(opt) {
						if (opt.selected) newgrp = opt.value;
					});
					var post = {
						Target: target,
						Key: key,
						Perms: vals.join(','),
						Group: newgrp
					};
						
					pr.send('/youpi/permissions/set/', $H(post).toQueryString());
					
					//Modalbox.hide(); 
				});
				$('modalbox_reset_input').observe('click', function() { 
					// Reset to user's default permissions
					// Gets default user permissions
					var pr = new HttpRequest(
						null,
						null,
						function(r) {
							if (r.Error) {
								return;
							}
							userInfo.groupname = r.default_group;
							$('modalbox_tab_div').update(update_table(userInfo, r.perms));
						}
					);
					pr.send('/youpi/permissions/default/');
					Modalbox.validated = true;
				});
				$('modalbox_cancel_input').observe('click', function() { 
					Modalbox.hide(); 
				});
			}
		});
	}
};

/*
 * Function: get_permissions_from_data
 * Same as get_permissions() but with no XHR query. Data is passed instead.
 *
 * Parameters:
 *  data - object: must have the following members: 
 *   {isOwner: bool, mode: str, groupname: str, username: str, perms: object, groups: array}
 *  target - string: entity
 *  key - string
 *  misc - any: misc data passed to handler [optional]
 *
 *  Note that target and key are only used to set new permissions
 *
 * Returns:
 *  container DOM element
 *
 */ 
function get_permissions_from_data(data, target, key, handler, misc) {
	var handler = typeof(handler) == 'function' ? handler : null;
	var uid = 'user_permissions_div_' + Math.floor(Math.random() * 999999);
	var container = new Element('div', {id: uid});
	var r = data.evalJSON(sanitize = true);
	container.update(r.username).insert('/').insert(r.groupname);
	container.insert('  ').insert(r.mode);
	if (r.isOwner) {
		container.insert(' (');
		var a = new Element('a', {href: '#'}).update('Change');
		a.observe('click', function() {
			boxes.permissions(
				uid,
				handler,
				target, 
				String(key), 
				r.perms, 
				{username: r.username, groupname: r.groupname, groups: r.groups},
				misc
			);
		});
		container.insert(a).insert(')');
	}
	if (handler) handler(r, misc);

	return container;
}

/*
 * Function: get_permissions
 * Returns information about user permissions
 *
 * Parameters:
 *  target - string: entity
 *  key - string
 *  handler - function: callback function [optional]
 *  misc - any: misc data passed to handler [optional]
 *
 * Returns:
 *  container DOM element
 *
 */ 
function get_permissions(target, key, handler, misc) {
	var handler = typeof(handler) == 'function' ? handler : null;
	var post = {
		Target: target,
		Key: key
	};

	var uid = 'user_permissions_div_' + Math.floor(Math.random() * 999999);
	var container = new Element('div', {id: uid});
	var pr = new HttpRequest(
		container,
		null,
		function(r) {
			if (r.Error) {
				return;
			}

			container.update(r.username).insert('/').insert(r.groupname);
			container.insert('  ').insert(r.mode);
			if (r.isOwner) {
				container.insert(' (');
				var a = new Element('a', {href: '#'}).update('Change');
				a.observe('click', function() {
					boxes.permissions(
						uid,
						handler,
						post.Target, 
						post.Key, 
						r.perms, 
						{username: r.username, groupname: r.groupname, groups: r.groups},
						misc
					);
				});
				container.insert(a).insert(')');
			}
			if (handler) handler(r, misc);
		}
	);

	// Get tag permissions
	pr.send('/youpi/permissions/get/', $H(post).toQueryString());
	return container;
}

/*
 * Class: InputPathSelector
 * An extended read-only input text filed allowing to select a directory path
 *
 * Parameters:
 *  container - DOM node: parent DOM container
 *  startValue - string: title caption of the 'start' button
 *  onStartHandler - function: callback function to call when the 'start' button is clicked
 *  backHandler - function: callback function to call when the 'back' link is clicked [optional]
 *
 */ 
var InputPathSelector = Class.create({
	/*
	 * Var: _id
	 * Unique Id string
	 *
	 */
	_id: 'input_selector_' + Math.floor(Math.random() * 999999),
	/*
	 * Var: path
	 * Selected path
	 *
	 */
	path: null,
	/*
	 * Function: initialize
	 * Constructor
	 *
	 */
	initialize: function(container, startValue,  onStartHandler, backHandler) {
		if (typeof startValue != 'string')
			throw "Must be a string";
		if (typeof onStartHandler != 'function')
			throw "Handler must be a function";
		if (backHandler && typeof backHandler != 'function')
			throw "Handler must be a function";

		this.startValue = startValue;
		this.startHandler = onStartHandler;
		var patterns;

		var msg = 'Click to open the path selector';
		var pathi = new Element('input', {id: this._id + '_data_path_input', 
			readonly: 'readonly',
			type: 'text', 
			size: 50, 
			value: msg,
			title: msg}).addClassName('datapath').addClassName('text_disabled');
		var importb = new Element('input', {type: 'button', value: startValue});
		importb._handler = this.startHandler;
		importb.observe('click', function() { 
			this._handler(pathi.value, patterns);
		}).hide();
		pathi.observe('click', function() {
			boxes.browsePath(['*.*'], function(path, filePatterns) {
				if (path) {
					pathi.writeAttribute('value', path);
					patterns = filePatterns;
					importb.show();
					this.addClassName('text_enabled');
				}
			}.bind(this));
		});
		if (backHandler) {
			var backa = new Element('a', {href: '#'}).update('Back');
			backa.observe('click', function() { backHandler(); });
			container.update('(').insert(backa).insert(')');
		}
		container.insert(pathi).insert(importb).appear();
	}
});

/*
 * Class: BatchUploadWidget
 * A widget that allows to select a data path and to batch import all files
 * in this directory
 *
 * Parameters:
 *  container - DOM node: parent DOM container
 *  backHandler - function: callback function to call when the 'back' link is clicked [optional]
 *  onFinishHandler - function: callback function to call when the batch processing is over [optional]
 *
 */ 
var BatchUploadWidget = Class.create({
	/*
	 * Var: _id
	 * Unique Id string
	 *
	 */
	_id: 'upload_widget_' + Math.floor(Math.random() * 999999),
	_cancelImport: false,
	_backHandler: false,
	_onFinishHandler: false,
	/*
	 * Function: initialize
	 * Constructor
	 *
	 */
	initialize: function(container, postData, backHandler, onFinishHandler) {
		if (backHandler && typeof backHandler != 'function')
			throw "Handler must be a function";
		if (onFinishHandler && typeof onFinishHandler != 'function')
			throw "Handler must be a function";
		if (typeof postData != 'object')
			throw "postData must be an object";
		if (!postData.ServerPath)
			throw "postData must have a ServerPath member!";

		this._container = container;
		this._backHandler = backHandler;
		this._onFinishHandler = onFinishHandler;
		this._postData = postData;

		container.update();
		new InputPathSelector(container, 'Import!', 
			// Start handler
			function(path, patterns) {
				this._cancelImport = false;
				this._batchImport(path, patterns);
			}.bind(this),
			backHandler ? backHandler : null
		);
	},
	/*
	 * Function: _batchImport
	 * Sets things up for batch import
	 *
	 * Parameters:
	 *  path - string: path for searching files
	 *  patterns - array: array of regexp patterns
	 *
	 */ 
	_batchImport: function(path, patterns) {
		var cancelb = new Element('input', {id: this._id + '_cancel_button', type: 'button', value: 'Cancel'});
		cancelb._this = this;
		cancelb.observe('click', function() {
			boxes.confirm('Are you sure you want to cancel the import?', function() {
				this._cancelImport = true;
			}.bind(this._this));
		});

		var tab = new Element('table').setStyle({width: '100%'});
		var tr, td;
		tr = new Element('tr');
		td = new Element('td').setStyle({width: '100%', verticalAlign: 'middle'});
		var p = new Element('div');
		this._uploadPB = new ProgressBar(p, 0, {
			borderColor: 'grey', 
			color: 'lightblue',
			animate: false
		});
		var log = new Element('span', {id: this._id + '_upload_log'});
		var wlog = new Element('div', {id: this._id + '_warn_upload_log'}).setStyle({maxHeight: '100px', overflow: 'auto'});
		td.insert(p).insert(wlog).insert(log);
		tr.insert(td);

		td = new Element('td').insert(cancelb);
		tr.insert(td);
		tab.insert(tr);
		this._container.update(tab);
		// Start import
		this._do_Import(0, path, patterns);
	},
	/*
	 * Function: _do_Import
	 * Import files recursively from a directory
	 *
	 * Parameters:
	 *  pos - integer: file number (seek)
	 *  path - string: path for searching files
	 *  patterns - array: array of regexp patterns
	 *  total - integer: total file count [optional]
	 *  skipped - integer: total files skipped [optional]
	 *
	 */ 
	_do_Import: function(pos, path, patterns, total, skipped) {
		var container = $(this._id + '_upload_log');
		var wlog = $(this._id + '_warn_upload_log');
		var r = new HttpRequest(
			container,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var r = resp.result;
				var log = new Logger(container);
				if (r.error) {
					container.update();
					log.msg_error(r.error);
					return;
				}
				if (r.warnings) {
					var wl = new Logger(wlog);
					r.warnings.each(function(warn) {
						wl.msg_warning(warn);
					});
				}
				if (!this._cancelImport && r.pos < r.total) {
					this._uploadPB.setPourcentage(r.percent);			
					this._do_Import(r.pos, path, patterns, r.total, r.skipped);
				}
				else {
					container.update();
					if (this._cancelImport)
						log.msg_warning('Aborted. ' + r.pos + ' files imported');
					else {
						this._uploadPB.setPourcentage(100);
						log.msg_ok('Done. ' + r.total + ' files processed' + (r.total == 0 ? ' (<b>maybe not the right directory?</b>).' : '.'));
					}
					var but = $(this._id + '_cancel_button');
					if (this._backHandler) {
						but.writeAttribute('value', 'Close');
						but.stopObserving('click');
						but.observe('click', this._backHandler);
					}
					// Refresh content
					if(this._onFinishHandler) this._onFinishHandler();
				}
			}.bind(this)
		);

		var post = $H(this._postData);
		post.set('Path', path);
		post.set('Patterns', patterns.join(';'));

		if (pos) {
			post.set('Pos', pos);
			post.set('Total', total);
			post.set('Skipped', skipped);
		}

		r.setBusyMsg('Please wait while processing');
		r.send(post.get('ServerPath'), post.toQueryString());
	}
});

// Monitors notify events
document.observe('notifier:notify', function(event) {
	Notifier.notify(event.memo);
});

document.observe('permissions:updated', function(event) {
	var c = $(event.memo.container_id);
	if (!c) throw 'Permissions container not found';
	c.update(get_permissions(event.memo.target, event.memo.key, event.memo.handler, event.memo.misc /* misc data parameter */));
});

document.observe('dom:loaded', function() {
	// Common to every page: the user login name can be clicked in order to display
	// current user/group/mode permissions
	$$('div.toplevelmenu div.user span')[0].observe('click', function() {
		var r = new HttpRequest(
				null,
				null,	
				// Handle results
				function(resp) {
					Notifier.notify('Permissions: ' + resp.username + '/' + resp.default_group + ' @ ' + resp.perms_octal, 6);
				}
		);

		r.send('/youpi/permissions/default/');
	});
});

document.observe('q:loaded', function() {
	Q.set({ 
		fontSize: "10px",
		image_path: "/media/js/3rdParty/Q/images/q"
	});
	Informer = new Q.Informer({holderStyle: { 
		marginTop: '66px',
		position: "fixed", 
		right: "10px", 
		top: "10px", 
		width: "250px", 
		zIndex: 100001
	}});//{life: {warning: timeout/1000}});
}); 

var box_file_browser;

/*
 * Turns on multichecking capabilities for a selection of checkboxes
 */
var youpi = {
	multi_nodes_selection:  null
};

function enable_multi_checking(nodes) {
	youpi.multi_nodes_selection = nodes;
	nodes.invoke('observe', 'click', handle_multi_checking);
	nodes.each(function(node) {node.checked = false;});
}

function handle_multi_checking() {
	var nodes = youpi.multi_nodes_selection;
	if (window.shiftPressed) {
		// Shift + Mouse click
		// Finds first and last positions
		var first = 0, last = 0;
		nodes.each(function(check, k) {
			if (check == window.lastCheckItem) first = k;
			else if (check == this) last = k;
		}.bind(this));
		if (last < first) {
			var tmp = first;
			first = last;
			last = tmp;
		}
		// Finds related checkboxes
		nodes.each(function(check, k) {
			if (k > first && k <= last) {
				check.checked = window.lastCheckItem.checked;
			}
		});
	}
	else {
		// Saves last button check state
		window.lastCheckItem = this;
	}
}

