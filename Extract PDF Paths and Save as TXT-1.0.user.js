// ==UserScript==
// @name         Extract PDF Paths and Save as TXT
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Extract PDF download paths from onclick attributes and save them to a .txt file
// @author       ils94
// @match        https://sian.an.gov.br/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    function extractPDFPaths() {
        const anchors = document.querySelectorAll('a.help_pesquisa[onclick]');
        const pdfPaths = [];

        anchors.forEach(anchor => {
            const onclick = anchor.getAttribute('onclick');
            const match = onclick.match(/fjs_Link_download\('([^']+\.pdf)'/);
            if (match) {
                pdfPaths.push(match[1]);
            }
        });

        return pdfPaths;
    }

    function downloadTextFile(filename, content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function createButton() {
        const button = document.createElement('button');
        button.textContent = 'Save PDF Paths';
        button.style.position = 'fixed';
        button.style.top = '10px';
        button.style.right = '10px';
        button.style.zIndex = 9999;
        button.style.padding = '10px';
        button.style.backgroundColor = '#28a745';
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '5px';
        button.style.cursor = 'pointer';

        button.addEventListener('click', () => {
            const paths = extractPDFPaths();
            if (paths.length > 0) {
                downloadTextFile('pdf_paths.txt', paths.join('\n'));
                alert(`Saved ${paths.length} PDF path(s) to pdf_paths.txt`);
            } else {
                alert('No PDF paths found on this page.');
            }
        });

        document.body.appendChild(button);
    }

    window.addEventListener('load', createButton);
})();
