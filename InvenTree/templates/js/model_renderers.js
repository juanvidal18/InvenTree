/*
 * This file contains functions for rendering various InvenTree database models,
 * in particular for displaying them in modal forms in a 'select2' context.
 * 
 * Each renderer is provided with three arguments:
 * 
 * - name: The 'name' of the model instance in the referring model
 * - data: JSON data which represents the model instance. Returned via a GET request.
 * - parameters: The field parameters provided via an OPTIONS request to the endpoint.
 * - options: User options provided by the client
 */


// Renderer for "Company" model
function renderCompany(name, data, parameters, options) {

    var html = `<span>${data.name}</span> - <i>${data.description}</i>`;

    return html;
}


// Renderer for "StockItem" model
function renderStockItem(name, data, parameters, options) {

    // TODO - Include part detail, location, quantity
    // TODO - Include part image
}


// Renderer for "StockLocation" model
function renderStockLocation(name, data, parameters, options) {

    var html = `<span>${data.name}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    if (data.pathstring) {
        html += `<p><small>${data.pathstring}</small></p>`;
    }

    return html;
}


// Renderer for "Part" model
function renderPart(name, data, parameters, options) {

    var image = data.image;

    if (!image) {
        image = `/static/img/blank_image.png`;
    }

    var html = `<img src='${image}' class='select2-thumbnail'>`;
    
    html += ` <span>${data.full_name ?? data.name}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    return html;
}


// Renderer for "PartCategory" model
function renderPartCategory(name, data, parameters, options) {

    var html = `<span>${data.name}</span>`;

    if (data.description) {
        html += ` - <i>${data.description}</i>`;
    }

    if (data.pathstring) {
        html += `<p><small>${data.pathstring}</small></p>`;
    }

    return html;
}