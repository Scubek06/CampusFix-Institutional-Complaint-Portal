// Main JavaScript for CampusFix

$(document).ready(function () {

    /* ==============================
       Auto Hide Alerts
    ============================== */
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);


    /* ==============================
       Bootstrap Tooltips
    ============================== */
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );

    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });


    /* ==============================
       Bootstrap Popovers
    ============================== */
    const popoverTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="popover"]')
    );

    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });


    /* ==============================
       Delete Confirmation
    ============================== */
    $('.delete-confirm').on('click', function (e) {

        if (!confirm('Are you sure you want to delete this item?')) {
            e.preventDefault();
        }

    });


    /* ==============================
       Image Upload Preview
    ============================== */
    $('#images').on('change', function () {

        const preview = $('#image-preview');
        preview.html('');

        const files = this.files;

        if (!files.length) return;

        for (let i = 0; i < files.length; i++) {

            const file = files[i];

            if (!file.type.startsWith('image/')) continue;

            const reader = new FileReader();

            reader.onload = function (e) {

                const img = $('<img>')
                    .attr('src', e.target.result)
                    .addClass('img-thumbnail m-2')
                    .css({
                        width: '120px',
                        height: '120px',
                        objectFit: 'cover'
                    });

                preview.append(img);
            };

            reader.readAsDataURL(file);
        }

    });


    /* ==============================
       Dashboard Counter Animation
    ============================== */
    $('.counter').each(function () {

        const $this = $(this);
        const target = parseInt($this.attr('data-target')) || 0;

        $({ countNum: 0 }).animate(
            { countNum: target },
            {
                duration: 1500,
                easing: 'swing',
                step: function () {
                    $this.text(Math.floor(this.countNum));
                },
                complete: function () {
                    $this.text(this.countNum);
                }
            }
        );

    });


    /* ==============================
       Card Hover Animation
    ============================== */
    $('.card').hover(
        function () {
            $(this).addClass('shadow-lg');
        },
        function () {
            $(this).removeClass('shadow-lg');
        }
    );


    /* ==============================
       Complaint Item Hover
    ============================== */
    $('.complaint-item').hover(
        function () {
            $(this).css({
                transform: 'translateX(5px)',
                transition: '0.3s'
            });
        },
        function () {
            $(this).css({
                transform: 'translateX(0)'
            });
        }
    );


    /* ==============================
       Loading Spinner (Optional)
    ============================== */
    $(document).ajaxStart(function () {
        $('#loading-spinner').show();
    });

    $(document).ajaxStop(function () {
        $('#loading-spinner').hide();
    });

});