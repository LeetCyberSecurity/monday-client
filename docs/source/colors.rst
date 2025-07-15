..
    This file is part of monday-client.

    Copyright (C) 2024 Leet Cyber Security <https://leetcybersecurity.com/>

    monday-client is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    monday-client is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with monday-client. If not, see <https://www.gnu.org/licenses/>.

.. title:: Color Palette

.. _color-reference:

Color Palette
=============

Click any color below to copy its HEX code to your clipboard.

.. raw:: html

    <style>
        .color-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        .color-item {
            display: flex;
            align-items: center;
            padding: 0.8rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        .color-item:hover {
            background-color: #f5f5f5;
            cursor: pointer;
        }
        .color-swatch {
            width: 50px;
            height: 50px;
            border-radius: 4px;
            margin-right: 1rem;
        }
        .color-code {
            font-family: monospace;
            user-select: all;
        }
        .copy-feedback {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            display: none;
        }
        .color-usage {
            font-size: 0.9em;
            color: #666;
            margin-top: 0.3em;
        }
    </style>

    <div class="color-grid"></div>

    <div class="copy-feedback">Color code copied!</div>

    <script>
        const colors = [
            { hex: '#ff5ac4', usages: ['groups'] }, // light-pink
            { hex: '#ff158a', usages: ['groups'] }, // dark-pink
            { hex: '#bb3354', usages: ['groups'] }, // dark-red
            { hex: '#e2445c', usages: ['groups'] }, // red
            { hex: '#ff642e', usages: ['groups'] }, // dark-orange
            { hex: '#fdab3d', usages: ['groups'] }, // orange
            { hex: '#ffcb00', usages: ['groups'] }, // yellow
            { hex: '#cab641', usages: ['groups'] },
            { hex: '#9cd326', usages: ['groups'] }, // lime-green
            { hex: '#00c875', usages: ['groups'] }, // green
            { hex: '#037f4c', usages: ['groups'] }, // dark-green
            { hex: '#0086c0', usages: ['groups'] }, // dark-blue
            { hex: '#579bfc', usages: ['groups'] }, // blue
            { hex: '#66ccff', usages: ['groups'] }, // turquoise
            { hex: '#a25ddc', usages: ['groups'] }, // purple
            { hex: '#784bd1', usages: ['groups'] }, // dark-purple
            { hex: '#7f5347', usages: ['groups'] }, // brown
            { hex: '#c4c4c4', usages: ['groups'] }, // grey
            { hex: '#808080', usages: ['groups'] }  // trolley-grey
        ];

        const colorGrid = document.querySelector('.color-grid');

        colors.forEach(({hex, usages}) => {
            const colorItem = document.createElement('div');
            colorItem.className = 'color-item';
            colorItem.onclick = () => copyColor(hex);

            const usageText = usages.join(', ');
            colorItem.innerHTML = `
                <div class="color-swatch" style="background-color: ${hex}"></div>
                <div>
                    <code class="color-code">${hex}</code>
                    <div class="color-usage">Used for: ${usageText}</div>
                </div>
            `;

            colorGrid.appendChild(colorItem);
        });

        function copyColor(color) {
            navigator.clipboard.writeText(color);
            const feedback = document.querySelector('.copy-feedback');
            feedback.style.display = 'block';
            setTimeout(() => {
                feedback.style.display = 'none';
            }, 2000);
        }
    </script>
