$('.oper_btn').each(function () {
        // 获取支付状态
        status = $(this).attr('status')
        if (status == 1){
            $(this).text('去支付')
        }
        else if (status == 4){
            $(this).text('去评价')
        }
        else if (status == 5){
            $(this).text('已完成')
        }
    })

$('.oper_btn').click(function () {
    // 获取status
    var status = $(this).attr('status')
    // 获取订单id
    var order_id = $(this).attr('order_id')
    if(status == 1){
        // 进行支付
        // 发起 ajax post 请求，访问/order/pay,传递参数：order_id
        var csrf = $('input[name="csrfmiddlewaretoken"]').val()
        // 组织参数
        var params = {'order_id': order_id, 'csrfmiddlewaretoken': csrf}
        $.post('/order/pay', params, function (data) {
            if(data.res == 3){
                // 引导用户到支付页面
                window.open(data.pay_url)
                // 浏览器访问/order/check,获取交易支付的结果
                // ajax post 传递参数:order_id
                $.post('/order/check', params, function (data) {
                    if(data.res == 3){
                        alert('支付成功')
                        // 刷新页面
                        location.reload()
                    }else{
                        alert(data.errmsg)
                    }
                })
            }else{
                alert(data.errmsg)
            }
        })
    }else if (status == 4){
        // 其他情况
        // 跳转到评价页面
        location.href = '/order/comment/'+order_id
    }
})





