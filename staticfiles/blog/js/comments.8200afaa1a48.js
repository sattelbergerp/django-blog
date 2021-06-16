
function addVoteHandlers(name, type){
    forms = $(name)
    for( var i = 0; i < forms.length; i++){
        $('#'+forms[i].id).submit(function(event){
            event.preventDefault();
            vote(event.target, event.target.dataset.id, type)
            
        })
    }
}

function compactInt(value){
    let exp = Math.floor(Math.log(Math.abs(value)) / Math.log(1000));
    chars = 'KMBTQ';
    if(exp > chars.length || exp < 1)
        return value;
    let char = chars[exp-1];
    return fmtDecimal(Math.pow(value/1000, exp)) + '' + char;
}

function fmtDecimal(decimal){
    text = String(decimal).split('.');
    if (text.length == 2 && text[1][0] !== '0') 
        return text[0] + '.' + text[1][0];
    else
        return text[0];
}

function vote(target, id, type){
    var csrf = $('#'+target.id+' input[name="csrfmiddlewaretoken"]').val()
    $.post(target.action, {
        csrfmiddlewaretoken: csrf,
        type: type,
    });

    var votes = Number($('#comment-'+id+'-votes').data().votes);
    var upvoted = $('#'+id+'-icon-u').hasClass('bi-arrow-up-square-fill');
    var downvoted = $('#'+id+'-icon-d').hasClass('bi-arrow-down-square-fill');

    if(type==='u' && upvoted){
        $('#'+id+'-icon-u').removeClass('bi-arrow-up-square-fill');
        $('#'+id+'-icon-u').addClass('bi-arrow-up-square');
        votes-=1;
    }else if(type==='d' && downvoted){
        $('#'+id+'-icon-d').removeClass('bi-arrow-down-square-fill');
        $('#'+id+'-icon-d').addClass('bi-arrow-down-square');
        votes+=1;
    }else if(type=='u'){
        $('#'+id+'-icon-u').removeClass('bi-arrow-up-square');
        $('#'+id+'-icon-u').addClass('bi-arrow-up-square-fill');
        if(downvoted){
            $('#'+id+'-icon-d').removeClass('bi-arrow-down-square-fill');
            $('#'+id+'-icon-d').addClass('bi-arrow-down-square');
            votes += 1
        }
        votes += 1;
    }else if(type=='d'){
        $('#'+id+'-icon-d').removeClass('bi-arrow-down-square');
        $('#'+id+'-icon-d').addClass('bi-arrow-down-square-fill');
        if(upvoted){
            $('#'+id+'-icon-u').removeClass('bi-arrow-up-square-fill');
            $('#'+id+'-icon-u').addClass('bi-arrow-up-square');
            votes -= 1
        }
        votes -= 1;
    }
    $('#comment-'+id+'-votes').data('votes', votes);
    $('#comment-'+id+'-votes').html(compactInt(votes));
    
}

$(document).ready(function(){
    addVoteHandlers('.comment-upvote-form', 'u')
    addVoteHandlers('.comment-downvote-form', 'd')
})