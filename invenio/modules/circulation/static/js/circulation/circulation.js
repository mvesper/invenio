/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

define(
    [
        'jquery',
        'hgn!js/circulation/templates/item_brief',
        'hgn!js/circulation/templates/user_brief',
        'hgn!js/circulation/templates/record_brief',
        'hgn!js/circulation/templates/item',
        'hgn!js/circulation/templates/library',
        'hgn!js/circulation/templates/mail_template',
        'hgn!js/circulation/templates/loan_cycle',
        'hgn!js/circulation/templates/entity_functions',
    ],
function($, item_template, user_template, record_template, t_item, t_library, t_mail, t_loan, entity_functions) {

    var entity_templates = {'item': t_item,
                            'record': record_template,
                            'user': user_template,
                            'library': t_library,
                            'mail_template': t_mail,
                            'loan_cycle': t_loan};

    function get_entity(){
        var url_parts = document.URL.split('/');
        return url_parts[url_parts.length -1];
    }

    function get_entity_id(){
        var url_parts = document.URL.split('/');
        return [url_parts[url_parts.length -2],
                url_parts[url_parts.length -1]];
    }

    function action_validate_result(data){
        data = JSON.parse(data);
        var res = [];

        record_items = data.record_items;

        for (var key in data) {
            if (key == 'record_items') {
                continue;
            }

            var id = '#'+key+'_button';
            var errors = data[key];
            var element = $(id);

            if (errors.length == 0) {
                element.removeClass('btn-danger').removeClass('btn-success').addClass('btn-default');
                element.prop('disabled', true);
            } else {
                var fail = false;
                for (var i=0; i < errors.length; i++) {
                    var error_message = [];
                    if (errors[i] !== true) {
                        error_message.push(errors[i]);
                        fail = true;
                    }

                    if (fail == true) {
                        element.removeClass('btn-default').removeClass('btn-success').addClass('btn-danger');
                        element.prop('disabled', false);
                        element.prop('title', error_message.join('\n'));
                    } else {
                        element.removeClass('btn-default').removeClass('btn-danger').addClass('btn-success');
                        element.prop('disabled', false);
                        element.prop('title', '');
                    }
                }
            }
        }
    }

    var user = [];
    var item = [];
    var record = [];
    var record_items = {'loan': [], 'request': []};

    function populate_circulation_search(data){
        try{
            data = JSON.parse(data);
            user = user.concat(data.user);
            item = item.concat(data.items);
            record = record.concat(data.records);
        } catch(error) {}

        $('#circulation_item').html(item_template({'entities': item}));
        $('#circulation_user').html(user_template({'entities': user}));
        $('#circulation_record').html(record_template({'entities': record}));

        var search_body = {'user': user,
                           'items': item,
                           'records': record,
                           'start_date': $('#circulation_date_from').val(),
                           'end_date': $('#circulation_date_to').val()}

        $.ajax({
            type: "POST",
            url: "/circulation/api/circulation/try_actions",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: action_validate_result,
            contentType: 'application/json',
        });
    }

    $('#circulation_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var search_body = {'search': {}, 'entity': get_entity()}

            var search = $('#circulation_search').val();
            var search_parts = search.split(' ');

            for(var i = 0; i < search_parts.length; i++){
                try {
                    var search_part = search_parts[i];
                    var splited = search_part.split('=');
                    var key = splited[0].replace(' ', '');
                    var value = splited[1].replace(' ', '');
                    search_body.search[key] = value;
                } catch (err) {}
            }

            $.ajax({
                type: "POST",
                url: "/circulation/api/circulation/search",
                data: JSON.stringify(JSON.stringify(search_body)),
                success: populate_circulation_search,
                contentType: 'application/json',
            });
        }
    });


    function populate_entity_search(data){
        data = JSON.parse(data);
        var entity = get_entity();
        $('#entity_search_result').html(entity_templates[entity]({'entities': data}));
    };

    $('#entity_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var url_parts = document.URL.split('/');
            var entity = url_parts[url_parts.length -1];

            var search_body = {'entity': entity, 'search': {}}

            var search = $('#entity_search').val();
            var search_parts = search.split(' ');

            for(var i = 0; i < search_parts.length; i++){
                try {
                    var search_part = search_parts[i];
                    var splited = search_part.split('=');
                    var key = splited[0].replace(' ', '');
                    var value = splited[1].replace(' ', '');
                    search_body.search[key] = value;
                } catch (err) {}
            }

            $.ajax({
                type: "POST",
                url: "/circulation/api/entity/search",
                data: JSON.stringify(JSON.stringify(search_body)),
                success: populate_entity_search,
                contentType: 'application/json',
            });
        }
    });

    var json_editor = null;

    $('#entity_create').ready(function() {
        if ($('#entity_create').length == 0) {
            return;
        }

        var entity = get_entity();

        function start_json_editor(data) {
            var data = JSON.parse(data);
            var schema = data['schema'];
            delete schema.properties.id;
            json_editor = new JSONEditor($('#entity_create')[0], 
                    {
                        schema: data['schema'],
                        theme: 'bootstrap3',
                        no_additional_properties: true,
                    });
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/get_json_schema",
            data: JSON.stringify(JSON.stringify({'entity': entity})),
            success: start_json_editor,
            contentType: 'application/json',
        });
    });

    $('#entity_create_button').on("click", function(event){
        var entity = get_entity();
        var json = json_editor.getValue();

        var search_body = {'entity': entity, 'data': json}

        function success(data) {
            var msg = 'Successfully created a new entity.'
            $.notify(msg, 'success');
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/create",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: success,
            contentType: 'application/json',
        });
    });
    
    $('#entity_update').on("click", function(event){
        var data = get_entity_id();
        var entity = data[0];
        var id = data[1];
        var json = json_editor.getValue();

        var search_body = {'entity': entity, 'id': id, 'data': json}

        function success(data) {
            var msg = 'Successfully updated the following entity: ' +
                      entity + ' ' + id;
            $.notify(msg, 'success');
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/update",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: success,
            contentType: 'application/json',
        });
    });

    $('#entity_detail').ready(function() {
        if ($('#entity_detail').length == 0) {
            return;
        }
        var data = get_entity_id();
        entity = data[0];
        id = data[1];

        function start_json_editor(data) {
            data = JSON.parse(data);
            json_editor = new JSONEditor($('#entity_detail')[0], 
                    {
                        schema: data['schema'],
                        theme: 'bootstrap3',
                        no_additional_properties: true,
                    });

            json_editor.setValue(data['data']);
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/get",
            data: JSON.stringify(JSON.stringify({'entity': entity, 'id': id})),
            success: start_json_editor,
            contentType: 'application/json',
        });
    });

    $('#entity_actions').ready(function() {
        if ($('#entity_actions').length == 0) {
            return;
        }
        var data = get_entity_id();
        entity = data[0];
        id = data[1];

        function show_entity_functions(data) {
            data = JSON.parse(data);
            $('#entity_actions').html(entity_functions({'functions': data['data']}));
        }
        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/get_functions",
            data: JSON.stringify(JSON.stringify({'entity': entity, 'id': id})),
            success: show_entity_functions,
            contentType: 'application/json',
        });
    });

    $('#entity_actions').on("click", function(event){
        var data = get_entity_id();
        var entity = data[0];
        var id = data[1];
        var func = event.target.id;

        function yay(data) {
            alert('yay');
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/run_action",
            data: JSON.stringify(JSON.stringify({'entity': entity, 'id': id, 'function': func})),
            success: yay,
            contentType: 'application/json',
        });
    });
    
    $('#entity_new').on("click", function(event){
        var entity = get_entity();
        window.location.href = '/circulation/entities/create/' + entity;
    });

    $('#entity_search_result').on("click", ".entity_delete", function(event){
        var entity = get_entity();
        var id = event.target.id.split('_')[1];
        var element = $('#'+entity+'_'+id);
        $.notify.addStyle('confirm_deletion', {
            html: "<div><div class='btn-group' role='group' style='width: 200px'>" +
                        "<button type='button' id='notify_deletion_confirm_"+id+"' class='btn btn-success'>" +
                            "<span class='glyphicon glyphicon-ok'></span>" +
                        "</button>" +
                        "<button type='button' id='notify_deletion_cancel_"+id+"' class='btn btn-danger '>" +
                            "<span class='glyphicon glyphicon-remove'></span>" +
                        "</button>" +
                  "</div></div>"
        });

        $(event.target).notify({}, 
                               {style: 'confirm_deletion',
                                autoHide: false,
                                clickToHide: false,
                                position: 'right middle'});

        $(document).on('click', '#notify_deletion_confirm_'+id, function(event){
            function success(data) {
                var msg = 'Successfully deleted the following entity: ' +
                          entity + ' ' + id;
                $.notify(msg, 'success');
                $(this).trigger('notify-hide');
                element.hide(500, function(){element.remove();});
            }

            var search_body = {'entity': entity, 'id': id};
            $.ajax({
                type: "POST",
                url: "/circulation/api/entity/delete",
                data: JSON.stringify(JSON.stringify(search_body)),
                success: success,
                contentType: 'application/json',
            });
        })

        $(document).on('click', '#notify_deletion_cancel_'+id, function(event){
            $(this).trigger('notify-hide');
        })
    });

    $('#circulation_search_result').on("click", ".entity_delete", function(event){
        var id = event.target.id.split('_')[1];
        var parentElement = event.target.parentNode;
        while(!parentElement.id.lastIndexOf('circulation', 0) == 0){
            parentElement = parentElement.parentElement;

        }
        var kind = parentElement.id.split('_')[1];
        var list = null;
        if (kind == 'item') {
            list = item;
        }
        if (kind == 'record') {
            list = record;
        }
        if (kind == 'user') {
            list = user;
        }

        var i = 0;
        for (i = 0; i < list.length; i++){
            var tmp = list[i];
            if (tmp.id == id){
                break;
            }
        }

        list.splice(i, 1);
        populate_circulation_search({});
    });

    $('#circulation_validation').on("click", ".btn", function(event){
        var action = $(event.target).attr('id').split('_')[0];
        var items = item.map(function(x){return x.id});
        items = items.concat(record_items[action]).filter(function(x){return x != undefined});

        try {
            var user_id = user[0].id;
        } catch(err) {
            var user_id = null;
        }

        function clear_circulation(data) {
            $('#circulation_validation_body').html('');
            //$('#circulation_validation').hide();
            $('#circulation_user').html('');
            $('#circulation_item').html('');
            $('#circulation_record').html('');

            user = [];
            item = [];
            record = [];

            $.notify('Successfully '+action+'ed the following items: '+items.join(', '), 'success');
        }

        var search_body = {'action': action,
                           'user': user_id,
                           'items': items,
                           'start_date': $('#circulation_date_from').val(),
                           'end_date': $('#circulation_date_to').val()}

        $.ajax({
            type: "POST",
            url: "/circulation/api/circulation/run_action",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: clear_circulation,
            contentType: 'application/json',
        });
    });

    var from = new Date();
    var to = new Date();
    to.setDate(to.getDate() + 28);
    $('#circulation_date_from').datepicker({ dateFormat: 'dd/mm/yy' });
    $('#circulation_date_from').datepicker('setDate', from);
    $('#circulation_date_to').datepicker({ dateFormat: 'dd/mm/yy' });
    $('#circulation_date_to').datepicker('setDate', to);
}
);
