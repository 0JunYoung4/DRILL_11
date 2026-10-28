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
$titleFont = [System.Drawing.Font]::new('Malgun Gothic', 34, [System.Drawing.FontStyle]::Bold)
$stateFont = [System.Drawing.Font]::new('Malgun Gothic', 28, [System.Drawing.FontStyle]::Bold)
$font = [System.Drawing.Font]::new('Malgun Gothic', 20)
$smallFont = [System.Drawing.Font]::new('Malgun Gothic', 17)
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
    $canvas.DrawString('DRILL 11 | 소년 상태 다이어그램', $titleFont, $ink, 65, 38)
    $canvas.DrawString('입력 이벤트, 시간 제한 및 화면 경계 자동 방향 전환', $font, $ink, 70, 102)

    $canvas.FillEllipse($ink, 275, 176, 25, 25)
    Arrow @(287, 202, 287, 240)
    State '대기 (IDLE)' "서 있는 애니메이션`n진입 시 대기 시간 초기화" 80 240 '#315D95'
    State '자동 무적 런' "AUTORUN | 속도·크기 2배`n키 조작 없이 자동 이동" 900 240 '#A83F22'
    State '수면 (SLEEP)' "잠자는 자세`n이동하지 않음" 80 730 '#5D5688'
    State '달리기 (RUN)' "기본 속도·크기`n마지막에 누른 방향키 우선" 900 730 '#287363'

    Arrow @(500, 295, 900, 295)
    Label 'a 키 누름' 560 248 280 42
    Arrow @(900, 405, 500, 405)
    Label '자동 무적 런 5초 이상 경과' 530 414 340 42

    Arrow @(1320, 275, 1475, 275, 1475, 190, 1110, 190, 1110, 240)
    Label "화면 좌우 끝에 도달`n이동 방향 자동 반전" 1160 122 370 62

    Arrow @(1110, 470, 1110, 730)
    Label "왼쪽 / 오른쪽 방향키 누름`n자동 무적 런 취소" 1130 555 350 65

    Arrow @(210, 470, 210, 730)
    Label "대기 시간`n5초 이상 경과" 80 558 220 68
    Arrow @(390, 730, 390, 470)
    Label '스페이스 키 누름' 305 650 235 42

    Arrow @(500, 460, 650, 605, 900, 770)
    Label '왼쪽 / 오른쪽 방향키 누름' 515 540 340 42
    Arrow @(900, 885, 590, 885, 590, 490, 500, 490, 500, 455)
    Label "누르고 있던 방향키를`n모두 놓음" 510 760 240 65
    Arrow @(500, 940, 900, 940)
    Label '왼쪽 / 오른쪽 방향키 누름' 525 960 350 42

    $canvas.DrawString('시간 만료 시 대기 시간을 새로 측정합니다. 방향키로 취소하면 기본 속도와 크기로 돌아갑니다.',
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
