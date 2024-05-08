var html =
'    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />'+
'    <link rel="stylesheet" href="http://127.0.0.1:6001/static/assets/css/bot.css">'+
'    <div class="chatting-environment" id="chatting-environment">'+
'        <div class="chat-board">'+
'            <div class="chat-board__top">'+
'                <h3 class="top-heading">NeoBot</h3>'+
'            </div>'+
'            <div class="chat-board__chatting-area" id="staging">'+
''+
'            </div>'+
'            <div class="chat-board__bottom">'+
'                <div class="chat-input  ">'+
'                    <div class="input-sec">'+
'                        <input type="text" id="txtInput" placeholder="Type a message..." autofocus />'+
'                        <button type="button" onclick="send_msg_stag()" name="submit" id="press_enter_stag" hidden="">SUBMIT</button>'+
'                    </div>'+
'                    <div class="send" onclick="check_data_stag()">'+
'                        <img src="http://127.0.0.1:6001/static/assets/img/icons/send-icon.png" alt="send-icon">'+
'                    </div>'+
'                </div>'+
'            </div>'+
'        </div>'+
'        <div class="close-btn" onclick=logo_rotate()>'+
'            <span class="material-symbols-outlined">chat</span>'+
'        </div>'+
'    </div>'+
'    <div class="error-environment" style="display: none;" id="error-environment">'+
'        <div class="chat-board">'+
'            <div class="chat-board__top">'+
'                <h3 class="top-heading">Staging Environment</h3>'+
'            </div>'+
'            <div class="chat-board__chatting-area" id="error">'+
''+
'             <div class="particular-chat-wrapper">'+
'                    <h4 class="chat user1">Access Denied. Please contact admin</h4>'+
'                </div>'+
'            </div>'+
'        </div>'+
'        <div class="close-btn-error" onclick=logo_rotate()>'+
'            <span class="material-symbols-outlined">chat</span>'+
'        </div>'+
'    </div>';

document.addEventListener("DOMContentLoaded", function(){
    $('body').append(html)
});
function logo_rotate(){
    var ip = location.host;
    var email = 'sumit.desai@neosoftmail.com'
//    var email = 'sumit.desai@mail.com'
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:6001/user_login",
        data: { ip: ip, email:email},
        success: function (result) {
        $(".chatting-environment .chat-board").toggle();
            if(result == '1'){
                if ($(".close-btn span").text() == "close") {
                    $(".close-btn span").text("chat");
                    $(".close-btn span").css('transform', 'rotate(90deg)');
                    $('.close-btn').animate(
                        { deg: -90 },
                        {
                            duration: 300,
                            step: function (now) {
                                $(this).css({ transform: 'rotate(' + now + 'deg)' });
                            }
                        }
                    );
                }
                else {
                    $(".close-btn span").text("close");
                    $(".close-btn span").css('transform', 'rotate(-90deg)');
                    $('.close-btn').animate(
                        { deg: 0 },
                        {
                            duration: 300,
                            step: function (now) {
                                $(this).css({ transform: 'rotate(' + now + 'deg)' });
                            }
                        }
                    );
                }
            }else{
                $('#error-environment').show()
                $('#chatting-environment').hide()
                $(".error-environment .chat-board").toggle();
                if ($(".close-btn-error span").text() == "close") {
                    $(".close-btn-error span").text("chat");
                    $(".close-btn-error span").css('transform', 'rotate(90deg)');
                    $('.close-btn-error').animate(
                        { deg: -90 },
                        {
                            duration: 300,
                            step: function (now) {
                                $(this).css({ transform: 'rotate(' + now + 'deg)' });
                            }
                        }
                    );
                }
                else {
                    $(".close-btn-error span").text("close");
                    $(".close-btn-error span").css('transform', 'rotate(-90deg)');
                    $('.close-btn-error').animate(
                        { deg: 0 },
                        {
                            duration: 300,
                            step: function (now) {
                                $(this).css({ transform: 'rotate(' + now + 'deg)' });
                            }
                        }
                    );
                }
            }
        }
    });

}

function send_msg_stag(){
    var msg = $('#txtInput').val()
    len_count = $("#txtInput").val().length
    if(len_count < 200 && (Boolean(msg.match(/[a-zA-Z0-9]+/)))){
        $("#txtInput").attr('disabled','disabled');
    }else{
        if(len_count > 200){
            $("#staging").append("<div class='d-flex class particular-chat-wrapper'><h4 class='chat user1' style='color:red'>Chat message is too large </h4></div>")
        }else{
            $("#staging").append("<div class='d-flex class particular-chat-wrapper'><h4 class='chat user1' style='color:red'>Invalid Input </h4></div>")
        }
        $('#staging').scrollTop($('#staging')[0].scrollHeight);
    }
    if(msg != '' && len_count < 200 && (Boolean(msg.match(/[a-zA-Z0-9]+/))) ) {
     $("#staging").append("<div class='d-flex class particular-chat-wrapper'><h4 class='chat user2'>"+msg+"</h4></div>")
     $('#txtInput').val("")
     $('#txtInput').attr('disabled','disabled');
        $.ajax({
            type: "POST",
            url: "http://127.0.0.1:6001/bot_msg",
            data: { msg: msg,type:'stag'},
            success: function (result) {
                $("#txtInput").removeAttr('disabled');
                $("#staging").append(result)
                $('#staging').scrollTop($('#staging')[0].scrollHeight);
            }
        });
    }
}

function button_intent_stag(intent,title){
    var msg = intent
    $("#staging").append("<div class='d-flex class particular-chat-wrapper'><h4 class='chat user2'>"+title+"</h4></div>")
    $('#txtInput').val("")
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:6001/bot_msg",
        data: { msg: msg,type:'stag'},
        success: function (result) {
            $('#rm_stag').remove()
            $("#staging").append(result)
            $('#staging').scrollTop($('#staging')[0].scrollHeight);
        }
    });
}

function check_data_stag(){
    $('#press_enter_stag').click();
}
$(document).ready(function(){
    $('#txtInput').keypress(function(e){
      if(e.keyCode==13)
      $('#press_enter_stag').click();
    });
});