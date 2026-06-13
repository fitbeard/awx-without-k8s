function envoy_on_response(handle)
    -- This script rewrites urls in the response by replacing the service base path
    -- in Location headers and in the request body.
    -- ex: translates /service-path/galaxy/ to /gateway-path/hub/ in service response bodies
    handle:logDebug("Running lua script to rewrite response body.")
    -- Ignore this script if the response is an upgrade response to prevent websockets from breaking
    local status_code = handle:headers():get(":status")
    if status_code == "101" then
        return
    end

    -- Ignore this script if the response is from a StreamingHTTPResponse event-stream
    local ctype = handle:headers():get("content-type")
    if ctype and string.match(ctype, "text/event%-stream") then
        handle:headers():replace("X-Accel-Buffering", "no")
        return
    end

    local location = handle:headers():get("Location")

    -- If the location contains __gateway_no_rewrite__=1 (e.g. as a GET param),
    -- then do not rewrite the location header.
    if location and string.match(location, "__gateway_no_rewrite__=1") then
        return
    end

    local prefix_rewrite = handle:metadata():get("prefix")
    local prefix = handle:metadata():get("prefix_rewrite")

    if location then
        local new_location = string.gsub(location, prefix, prefix_rewrite)
        handle:headers():replace("Location", new_location)
    end
    local body = handle:body()
    if body then
        body_bytes = body:getBytes(0, body:length())
        local modified_body = string.gsub(body_bytes, prefix, prefix_rewrite)

        local content_length = handle:body():setBytes(modified_body)
        handle:headers():replace("content-length", content_length)
    end
end

function envoy_on_request(handle)
    -- Translate urls in the request body back to the service's base path.
    -- ex: translates /gateway-path/hub/ to /service-path/galaxy/ in service request bodies
    handle:logDebug("Running lua script to rewrite request body.")

    -- Ignore this script if the request is an upgrade request to prevent websockets from breaking
    local upgrade_header = handle:headers():get("upgrade")
    if upgrade_header then
        return
    end

    local prefix_rewrite = handle:metadata():get("prefix")
    local prefix = handle:metadata():get("prefix_rewrite")

    local path = handle:headers():get(":path")
    if string.match(path, "=") then
        -- need to escape "-"
        local match = "%=" .. string.gsub(prefix_rewrite, "%-", "%%-")
        local replace = "%=" .. string.gsub(prefix, "%-", "%%-")

        handle:logDebug(match)
        handle:logDebug(replace)

        local new_path = string.gsub(path, match, replace)

        -- if the query param is urlencoded, replace those instead
        new_path = string.gsub(new_path, string.gsub(match, "/", "%%%%2F"), string.gsub(replace, "/", "%%%%2F"))

        handle:headers():replace(":path", new_path)
    end

    local body = handle:body()
    if body then
        body_bytes = body:getBytes(0, body:length())
        local modified_body = string.gsub(body_bytes, prefix_rewrite, prefix)

        local content_length = handle:body():setBytes(modified_body)
        handle:headers():replace("content-length", content_length)
    end
end
