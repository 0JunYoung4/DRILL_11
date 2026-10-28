param([string]$OutputPath = (Join-Path $PSScriptRoot '../state_diagram.png'))

# Optional documentation tool; requires Windows PowerShell and System.Drawing.
Add-Type -AssemblyName System.Drawing
$bitmap = [System.Drawing.Bitmap]::new(1600, 1100)
$canvas = [System.Drawing.Graphics]::FromImage($bitmap)
$canvas.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$canvas.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$canvas.Clear([System.Drawing.Color]::FromArgb(247, 249, 253))
$ink = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(28, 43, 65))
$white = [System.Drawing.Brushes]::White
$titleFont = [System.Drawing.Font]::new('Segoe UI', 34, [System.Drawing.FontStyle]::Bold)
$stateFont = [System.Drawing.Font]::new('Segoe UI', 28, [System.Drawing.FontStyle]::Bold)
$font = [System.Drawing.Font]::new('Segoe UI', 20)
$smallFont = [System.Drawing.Font]::new('Segoe UI', 17)
$pen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(80, 101, 130), 4)
$arrowCap = [System.Drawing.Drawing2D.AdjustableArrowCap]::new(5, 7)
$pen.CustomEndCap = $arrowCap
$center = [System.Drawing.StringFormat]::new()
$center.Alignment = [System.Drawing.StringAlignment]::Center
$center.LineAlignment = [System.Drawing.StringAlignment]::Center

function Label($text, $x, $y, $width = 370, $height = 65) {
    $rect = [System.Drawing.RectangleF]::new($x, $y, $width, $height)
    $canvas.FillRectangle([System.Drawing.Brushes]::WhiteSmoke, $rect)
    $canvas.DrawString($text, $smallFont, $ink, $rect, $center)
}

function Arrow([float[]]$coords) {
    $points = [System.Drawing.PointF[]]::new($coords.Length / 2)
    for ($i = 0; $i -lt $points.Length; $i++) {
        $points[$i] = [System.Drawing.PointF]::new($coords[2 * $i], $coords[2 * $i + 1])
    }
    $canvas.DrawLines($pen, $points)
}

function State($name, $detail, $x, $y, $color) {
    $brush = [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($color))
    $canvas.FillRectangle($brush, $x, $y, 420, 230)
    $canvas.DrawString($name, $stateFont, $white,
        [System.Drawing.RectangleF]::new($x, $y + 25, 420, 65), $center)
    $canvas.DrawString($detail, $font, $white,
        [System.Drawing.RectangleF]::new($x + 15, $y + 100, 390, 105), $center)
    $brush.Dispose()
}

try {
    $canvas.DrawString('DRILL 11 | Boy State Diagram', $titleFont, $ink, 65, 38)
    $canvas.DrawString('Events, timeouts and automatic boundary reflection', $font, $ink, 70, 102)

    $canvas.FillEllipse($ink, 275, 176, 25, 25)
    Arrow @(287, 202, 287, 240)
    State 'IDLE' "Standing animation`nIdle timer starts on entry" 80 240 '#315D95'
    State 'AUTORUN' "2x speed / 2x size`nRuns without held keys" 900 240 '#A83F22'
    State 'SLEEP' "Sleeping pose`nNo movement" 80 730 '#5D5688'
    State 'RUN' "Normal speed / size`nLatest held arrow wins" 900 730 '#287363'

    Arrow @(500, 295, 900, 295)
    Label 'a key down' 560 248 280 42
    Arrow @(900, 405, 500, 405)
    Label 'AutoRun elapsed >= 5 s' 530 414 340 42

    Arrow @(1320, 275, 1475, 275, 1475, 190, 1110, 190, 1110, 240)
    Label "Left / right boundary`nReverse direction" 1160 122 370 62

    Arrow @(1110, 470, 1110, 730)
    Label "Left / right key down`nCancel AutoRun" 1130 555 350 65

    Arrow @(210, 470, 210, 730)
    Label "Idle elapsed`n>= 5 s" 80 558 220 68
    Arrow @(390, 730, 390, 470)
    Label 'Space key down' 305 650 235 42

    Arrow @(500, 460, 650, 605, 900, 770)
    Label 'Left / right key down' 515 540 340 42
    Arrow @(900, 885, 590, 885, 590, 490, 500, 490, 500, 455)
    Label "All arrow keys`nreleased" 510 760 240 65
    Arrow @(500, 940, 900, 940)
    Label 'Left / right key down' 525 960 350 42

    $canvas.DrawString('Timeout returns to a fresh IDLE timer. Arrow cancellation restores normal speed and size.',
        $smallFont, $ink, 75, 1040)
    $bitmap.Save([System.IO.Path]::GetFullPath($OutputPath), [System.Drawing.Imaging.ImageFormat]::Png)
} finally {
    $center.Dispose()
    $pen.Dispose()
    $arrowCap.Dispose()
    $titleFont.Dispose()
    $stateFont.Dispose()
    $font.Dispose()
    $smallFont.Dispose()
    $ink.Dispose()
    $canvas.Dispose()
    $bitmap.Dispose()
}
