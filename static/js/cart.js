$(function (){
    // 计算被选中的商品的总件数和总价格
    function update_page_info() {
        // 获取所有被选中的商品的checkbox
        // 获取所有被选中的商品所在的ul元素
        var total_count = 0
        var total_price = 0
        $('.cart_list_td').find(':checked').parents('ul').each(function () {
            // 获取商品的数目和小计
            var count = $(this).find('.num_show').val()
            var amount = $(this).children('.col07').text()
            // 累加计算商品的总件数和总价格
            count = parseInt(count)
            amount = parseFloat(amount)
            total_count += count
            total_price += amount
        })
        // 设置被选中的商品的总件数和总价格
        $('.settlements').find('em').text(total_price.toFixed(2))
        $('.settlements').find('b').text(total_count)
    }

    // 计算商品的小计
    function update_goods_amount(sku_ul) {
        // 获取商品的价格和数量
        var count = sku_ul.find('.num_show').val()
        var price = sku_ul.children('.col05').text()
        // 计算商品的小计
        var amount = parseInt(count)*parseFloat(price)
        // 设置商品的小计
        sku_ul.children('.col07').text(amount.toFixed(2)+'元')
    }

    // 商品的全选和全不选
    $('.settlements').find(':checkbox').change(function () {
        // 获取全选的checkbox的选中状态
        var is_checked = $(this).prop('checked')
        // 遍历商品的对应的checkbox，设置这些checkbox的选中状态和全选的checkbox保持一致
        $('.cart_list_td').find(':checkbox').each(function () {
            $(this).prop('checked', is_checked)
        })
        // 更新页面的信息
        update_page_info()
    })

    // 反选。商品对应的checkbox状态发生改变时，设置全选checkbox的状态
    $('.cart_list_td').find(':checkbox').change(function () {
        // 获取页面上所有商品的数目
        var all_len = $('.cart_list_td').length
        // 获取页面上被选中的商品的数目
        var checked_len = $('.cart_list_td').find(':checked').length
        var is_checked = true
        if(checked_len < all_len){
            is_checked = false
        }
        $('.settlements').find(':checkbox').prop('checked', is_checked)
        // 更新页面的信息
        update_page_info()
    })



    // 更新购物车中商品的数量
    var error_update = false
    var total = 0
    function update_remote_cart_info(sku_id, count) {
        var csrf = $('input[name="csrfmiddlewaretoken"]').val()
        // 组织参数
        var params = {'sku_id':sku_id, 'count':count, 'csrfmiddlewaretoken':csrf}
        // 设置ajax请求为同步
        $.ajaxSettings.async = false
        // 发起ajax post请求，访问/cart/update, 传递参数:sku_id count
        // 默认发起的ajax请求都是异步的，不会等回调函数执行
        $.post('/cart/update', params, function (data) {
            if(data.res == 5){
                // 更新成功
                error_update = false
                total = data.total_count
            }else{
                // 更新失败
                error_update = true
                alert(data.errmsg)
            }
        })
        // 设置ajax请求为异步
        $.ajaxSettings.async = true
    }

    // 购物车商品数量的增加
    $('.add').click(function () {
        // 获取商品的id和商品的数量
        var sku_id = $(this).next().attr('sku_id')
        var count = $(this).next().val()

        // 组织参数
        count = parseInt(count)+1

        // 更新购物车记录
        update_remote_cart_info(sku_id, count)

        // 判断更新是否成功
        if(error_update == false){
            // 重新设置商品的数目
            $(this).next().val(count)
            // 计算商品的小计
            update_goods_amount($(this).parents('ul'))
            // 获取商品对应的checkbox的选中状态，如果被选中，更新页面信息
            var is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if(is_checked){
                // 更新页面信息
                update_page_info()
            }
            // 更新页面上购物车商品的总件数
            $('.total_count').children('em').text(total)
        }
    })

    // 购物车商品数量的减少
    $('.minus').click(function () {
        // 获取商品的id和商品的数量
        var sku_id = $(this).prev().attr('sku_id')
        var count = $(this).prev().val()

        // 校验参数
        count = parseInt(count)-1
        if(count <= 0){
            return
        }

        // 更新购物车中的记录
        update_remote_cart_info(sku_id, count)

        // 判断更新是否成功
        if(error_update == false){
            // 重新设置商品的数目
            $(this).prev().val(count)
            // 计算商品的小计
            update_goods_amount($(this).parents('ul'))
            // 获取商品对应的checkbox的选中状态，如果被选中，更新页面信息
            var is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if(is_checked){
                // 更新页面信息
                update_page_info()
            }
            // 更新页面上购物车商品的总件数
            $('.total_count').children('em').text(total)
        }
    })

    // 记录用户输入之前商品的数量
    var pre_count = 0
    $('.num_show').focus(function () {
        pre_count = $(this).val()
    })

    // 手动输入购物车中的商品数量
    $('.num_show').blur(function () {
        // 获取商品的id和商品的数量
        var sku_id = $(this).attr('sku_id')
        var count = $(this).val()

        // 校验参数
        if(isNaN(count) || count.trim().length==0 || parseInt(count)<=0){
            // 设置商品的数目为用户输入之前的数目
            $(this).val(pre_count)
            return
        }

        // 更新购物车中的记录
        count = parseInt(count)
        update_remote_cart_info(sku_id, count)

        // 判断更新是否成功
        if (error_update == false){
            // 重新设置商品的数目
            $(this).val(count)
            // 计算商品的小计
            update_goods_amount($(this).parents('ul'))
            // 获取商品对应的checkbox的选中状态，如果被选中，更新页面信息
            var is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if (is_checked){
                // 更新页面信息
                update_page_info()
            }
            // 更新页面上购物车商品的总件数
            $('.total_count').children('em').text(total)
        }else{
            // 更新失败，设置商品的数目为用户输入之前的数目
            $(this).val(pre_count)
        }

    })



    // 删除购物车记录
    $('.cart_list_td').children('.col08').children('a').click(function () {
        //获取商品id
        sku_id = $(this).parents('ul').find('.num_show').attr('sku_id')
        csrf = $('input[name="csrfmiddlewaretoken"]').val()
        // 组织参数
        params = {'sku_id': sku_id, 'csrfmiddlewaretoken': csrf}
        // 获取商品所在的ul元素
        sku_ul = $(this).parents('ul')
        // 发起Ajax post 请求，访问/cart/delete, 传递参数:sku_id
        $.post('/cart/delete', params, function (data) {
            if(data.res == 3){
                // 删除成功，移除页面上商品所在的ul元素
                sku_ul.remove() // 移除自身，包括子元素
                // 获取sku_ul中商品的选中状态
                is_checked = sku_ul.find(':checkbox').prop('checked')
                if(is_checked){
                    // 更新页面信息
                    update_page_info()
                }
                // 重新设置页面上购物车中商品的总件数
                $('.total_count').children('em').text(data.total_count)
            }else{
                alert(data.errmsg)
            }
        })
    })
})
