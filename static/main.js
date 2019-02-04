$('#shutdown').click(function(){
	$.get('shutdown');
	window.close();
});
$('#config').click(function(){
	$.get('configfile');
});
$('#openpath').click(function(){
	$.get('openpath');
});

if(navigator.userAgent.indexOf('Firefox')>-1){
	$.notify({
		message: 'Firefox请参考<a>https://github.com/URenko/Accesser/wiki/Firefox设置方法</a>进行手动设置',
		url: 'https://github.com/URenko/Accesser/wiki/Firefox%E8%AE%BE%E7%BD%AE%E6%96%B9%E6%B3%95'
		},{
			type: 'warning',
			delay: 10000
		});
}

let getlog = {
	url: 'log',
	dataType: 'json',
	success: function(data){
		if(data.level==='INFO'){$.notify({message:data.content},{type:'info',delay:10000});}
		else if(data.level==='WARNING'){$.notify({message:data.content},{type:'warning',delay:10000});}
		else if(data.level==='ERROR'){$.notify({message:data.content},{type:'danger',delay:10000});}
		$.post(getlog);
	},
	error: function(xhr, text){
		if(text==='timeout'){$.post(getlog);}
	}
};
$.post(getlog);
