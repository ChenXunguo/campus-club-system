// 校园社团活动管理系统 —— 全局脚本
document.addEventListener('DOMContentLoaded', function () {
    // 删除/危险操作确认
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // 自动隐藏提示消息
    document.querySelectorAll('.alert').forEach(function (alert) {
        if (!alert.classList.contains('alert-warning')) {
            setTimeout(function () {
                var bs = bootstrap.Alert.getOrCreateInstance(alert);
                bs.close();
            }, 5000);
        }
    });
});
