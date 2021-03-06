function login() {
    alert("歡迎進入 iOS Club");
    // if document.accpass.account
}

$(document).ready(function () {
    $('#btn_login').click(function () {
        let account = $('#input_account').val();
        let password = $('#input_pwd').val();
        let next = $('#next').val();
        jQuery.ajax({ //post form資料 抓取json檔案
            type: "POST",
            url: '/login',
            data: JSON.stringify({'account': account, 'password': password, 'next': next}), //post form
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (res) { //連到伺服器
                console.log(res['login']);
                console.log(res['next']);
                if (res['login'] == true) {
                    $(location).attr('href', res['next']);
                }
            },
            error: function (res) {
                console.log(res);
                Swal.fire({
                    icon: 'error',
                    title: "你是奇丁嗎？",
                    text: "你確定你記得你的密碼嗎？"
                });
            }
        });
    });
});