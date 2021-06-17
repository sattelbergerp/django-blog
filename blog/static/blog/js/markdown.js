function updateMarkdownPreview(element){
    $('#'+element.attr('id')+'-preview').html(window.md.render(element.val()));
}

$(document).ready(function(){
    window.md = window.markdownit();
    $(".markdown-editor").each(function( index ) {
        $(this).on('input', function () {
            updateMarkdownPreview($(this));
        });
        updateMarkdownPreview($(this));
    });
})