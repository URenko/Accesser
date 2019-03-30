$(document).ready(function(){
    $('#shutdown').click(function(){
        $.get('shutdown');
        window.close();
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
    
    $("#config").click(function(){
        $.post({
            type:"post",
            url:"get",
            success:function(data)
            {
                let settings = JSON.parse(data)["server"];
                //console.log(settings);
                for(let i in settings)
                {
                    let se = $(`#setting-form input[name='${i}']`);
                    if(se.attr("type") == "radio") // [enbale_LAN] 0.0.0.0 enable 127.0.0.1 disable;
                        $(`#setting-form input[name='${i}'][value='${settings[i]}']`).click();
                    else if(se.attr("type") == "text")
                        se.val(settings[i]);
                }
            }
        })
    })

    
    $("#settingModal .modal-footer .btn-primary").click(function()
    {
        console.log("Saving changes");
        let data={};
        $.each($("#settingModal input"), function(n, e){
            if(e.type == "radio" && e.checked || e.type != "radio")
                data["server." + e.name] = e.value;//parameters' names of getting and setting are inconsistent.
            
        });
        
        $.post({
            type:"POST",
            url:"set",
            data:data,
            success:function(data)
            {
                $.notify({message:"设置已保存"},{type:'info',delay:10000});
            },
            dataType:"json"
        });
    }
)

})