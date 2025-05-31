// ==UserScript==
// @name         Extract Unique PDF Titles and Links with Suffixes
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Extract unique PDF links from SIAN.
// @author       ils94
// @match        https://sian.an.gov.br/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function extractPDFItems() {
        const items = [];
        const seenPairs = new Set();
        const titleCount = {};
        const listItems = document.querySelectorAll('li');

        listItems.forEach(li => {
            const titleAnchor = li.querySelector('span.titulo_conteudo > a[onclick*="mudapagina_link"]');
            const pdfAnchors = li.querySelectorAll('a.help_pesquisa[onclick*="fjs_Link_download"]');

            if (!titleAnchor || pdfAnchors.length === 0) return;

            const rawTitle = titleAnchor.textContent.trim();

            pdfAnchors.forEach(anchor => {
                const onclick = anchor.getAttribute('onclick');
                const match = onclick.match(/fjs_Link_download\('([^']+\.pdf)'/);

                if (match) {
                    const link = match[1];
                    const key = `${rawTitle}::${link}`;

                    if (!seenPairs.has(key)) {
                        seenPairs.add(key);

                        // count and rename duplicates
                        titleCount[rawTitle] = (titleCount[rawTitle] || 0) + 1;
                        const finalTitle = titleCount[rawTitle] > 1 ?
                            `${rawTitle} - ${titleCount[rawTitle]}` :
                            rawTitle;

                        items.push({
                            title: finalTitle,
                            link: link
                        });
                    }
                }
            });
        });

        return items;
    }

    function downloadJSONFile(filename, jsonObject) {
        const content = JSON.stringify(jsonObject, null, 2);
        const blob = new Blob([content], {
            type: 'application/json'
        });
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
        button.textContent = 'SAVE PDF LINKS';
        button.style.position = 'fixed';
        button.style.top = '10px';
        button.style.right = '10px';
        button.style.zIndex = 9999;
        button.style.padding = '10px';
        button.style.backgroundColor = '#343a40';
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '5px';
        button.style.cursor = 'pointer';

        button.addEventListener('click', () => {
            const items = extractPDFItems();

            if (items.length > 0) {
                downloadJSONFile('pdf_links.json', items);
            } else {
                alert('No PDF links found.');
            }
        });

        document.body.appendChild(button);
    }

    window.addEventListener('load', createButton);
})();
