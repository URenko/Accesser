let NotifyLogger = 
{
    _loglevel:"INFO",
    _LoglevelPrior:["NOTSET",
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL"],
    _bl2fl:{
        NOTSET:"success",
        DEBUG:"success",
        INFO:"info",
        WARNING:"warning",
        ERROR:"danger",
        CRITICAL:"danger"
    },

    log(level, data, duration=10000)
    {
        level = level.toUpperCase();
        if(this._LoglevelPrior.indexOf(level) >= 
            this._LoglevelPrior.indexOf(this._loglevel))
        {
            $.notify({message:data},{type:this._bl2fl[level],delay:duration});
        }
    },
    setLogLevel(v)
    {
        this._loglevel = v.toUpperCase();
    }
}
$(document).ready(function(){

    let webuiSettings ={
        loglevel:"INFO"
    }
    if("Accesser" in localStorage)
    {
        webuiSettings = JSON.parse(localStorage.getItem("Accesser"));
    }
    NotifyLogger.setLogLevel(webuiSettings.loglevel);
    window.onunload=function()
    {
        localStorage["Accesser"] = JSON.stringify(webuiSettings);
    }


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
        timeout:0,
        success: function(data){
            NotifyLogger.log(data.level, data.content, 10000);
        },
        error: function(xhr, text){
            if(text==='timeout'){$.post(getlog);}
        },
        complete:function(xhr, result)
        {
            $.post(getlog);
            //console.log(result);
        }
    };
    $.post(getlog);
    
    $("#server-setting-form #DNS").change(function(e){
        let sel = $("#DNS-wrapper").get(0).children[1];
        let udf = $("#DNS-wrapper").get(0).children[2];
        if(e.target.value == "userDefine")
        {
            sel.classList.remove("col-sm-8");
            sel.classList.add("col-sm-3");
            udf.classList.remove("hidden");
            udf.classList.add("col-sm-5");
        }
        else
        {
            sel.classList.remove("col-sm-3");
            sel.classList.add("col-sm-8");
            udf.classList.remove("col-sm-5");
            udf.classList.add("hidden");
        }
    })
    
    //retrieve setting from server
    $("#config").click(function(){

        $.post({
            type:"post",
            url:"get",
            success:function(data)
            {
                let settings = JSON.parse(data);
                console.log(settings);
                let setFormByName = function(form, name, value)
                {
                    let se = $(`${form} *[name='${name}']`);
                    if(se.length == 0) return;
                    if(se.prop("tagName") == "INPUT")
                    {
                        if(se.attr("type") == "radio") 
                            $(`${form}  input[name='${name}'][value='${value}']`).click();
                        else if(se.attr("type") == "text")
                            se.val(value);
                    }
                    else if(se.prop("tagName") == "SELECT")
                    {
                        $.each(se.children(), function(n, e){
                            if(e.value == value)
                                e.selected = true;
                        })
                    }
                }
                //console.log(settings);
                for(let i in settings)
                {
                    if(settings[i] instanceof Object)
                    {
                        for(let j in settings[i])
                        {
                            setFormByName("#server-setting-form",`${i}.${j}`, settings[i][j] == null ? "":settings[i][j]);
                        }
                    }
                    else
                        setFormByName("#server-setting-form", i, settings[i]);
                }

                for(let i in webuiSettings)
                {
                    setFormByName("#webui-setting-form", `webui.${i}`, webuiSettings[i]);
                }
            }
        })
    })

    //Send settings to server.
    $("#settingModal .modal-footer .btn-primary").click(function()
    {
        console.log("Saving changes");
        //"ala.bla.cla" -> ala.bla.cla
        let setJSONSepe = function(data, name, value)
        {
            let dotPos = name.indexOf(".")
            if(dotPos > 0)
            {
                let nameFirst = name.substring(0, dotPos);
                if(!(nameFirst in data))
                {
                    data[nameFirst] = {};
                }
                setJSONSepe(data[nameFirst], name.substring(dotPos + 1, name.length), value);
            }
            else
            {
                data[name] = value;
            }

        }
        let data={};
        $.each($("#server-setting-form input"), function(n, e){
            if(e.type == "radio" && e.checked || e.type != "radio" && e.name !="DNS-userDefine")
                setJSONSepe(data, e.name, e.value);
        });
        $.each($("#server-setting-form select"), function(n, e)
        {
            if(e.name != "DNS")
                setJSONSepe(data, e.name, e.value);
        })
        if($("#DNS-wrapper select[name='DNS']").val() == "")
        {
            data["DNS"] = null;
        }
        else if($("#DNS-wrapper select").val() == "userDefine")
        {
            data["DNS"] = $("#DNS-wrapper input[name='DNS-userDefine']").val();
        }
        else
        {
            data["DNS"] = $("#DNS-wrapper select[name='DNS']").val();
        }

        webuiSettings["loglevel"] = $("#webui-setting-form select[name='webui.loglevel'").val();
        NotifyLogger.setLogLevel(webuiSettings["loglevel"]);
        console.log(data);
        
        $.post({
            type:"POST",
            url:"set",
            data:JSON.stringify(data),
            success:function(data)
            {
                if(data == -1)
                    NotifyLogger.log("ERROR", "保存设置失败", 10000);
                else if(data >= 0)
                    NotifyLogger.log("INFO", "保存设置成功", 10000);
                if(data > 0)
                    NotifyLogger.log("INFO", "等待服务器重启", 10000);
            },
            
            dataType:"json"
        });
    }
)

})