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
    ],
function($) {

    function get_entity_id(){
        var url_parts = document.URL.split('/');
        return [url_parts[url_parts.length -2],
                url_parts[url_parts.length -1]];
    }

    function get_entity_from_url(){
        var url_parts = document.URL.split('/');

        var part = null;
        for (var i=0; i < url_parts.length; i++){
            part = url_parts[i];
            if (part == 'entities') {
                return url_parts[i+1];
            }
        }
    }

    $('#entity_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var search_string = $('#entity_search').val();
            var url_encode = encodeURIComponent(search_string);
            var entity = get_entity_from_url();

            window.location.href = '/circulation/entities/'+entity+'/search/'+url_encode;
        }
    });

    $('#entity_new').on("click", function(event){
        var entity = get_entity_from_url();
        window.location.href = '/circulation/entities/'+entity+'/create/';
    });

    var json_editor = null;

    $('#entity_create').ready(function() {
        if ($('#entity_create').length == 0) {
            return;
        }

        var entity = get_entity_from_url();

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
        var entity = get_entity_from_url();
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
    

    $('#entity_search_result').on("click", ".entity_delete", function(event){
        var entity = get_entity_from_url();
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
}
);
