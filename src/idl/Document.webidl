/* -*- Mode: IDL; tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2 -*- */
/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * The origin of this IDL file is:
 * http://dom.spec.whatwg.org/#interface-document
 * http://www.whatwg.org/specs/web-apps/current-work/#the-document-object
 * http://dvcs.w3.org/hg/fullscreen/raw-file/tip/Overview.html#api
 * http://dvcs.w3.org/hg/pointerlock/raw-file/default/index.html#extensions-to-the-document-interface
 * http://dvcs.w3.org/hg/webperf/raw-file/tip/specs/PageVisibility/Overview.html#sec-document-interface
 * http://dev.w3.org/csswg/cssom/#extensions-to-the-document-interface
 * http://dev.w3.org/csswg/cssom-view/#extensions-to-the-document-interface
 *
 * http://mxr.mozilla.org/mozilla-central/source/dom/interfaces/core/nsIDOMDocument.idl
 */

enum VisibilityState { "hidden", "visible" };

/* http://dom.spec.whatwg.org/#interface-document */
[Constructor]
interface Document : Node {
};



