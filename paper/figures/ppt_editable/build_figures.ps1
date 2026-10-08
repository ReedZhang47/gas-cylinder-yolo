param([int[]]$Only = @(), [switch]$RefreshReview, [string]$Figures = '')
# Creates native PowerPoint shapes through COM. No flattened figure is inserted.
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$scenes = Get-Content -LiteralPath (Join-Path $taskRoot 'scene.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($Figures) { $Only = @($Figures -split ',' | ForEach-Object { [int]$_.Trim() }) }
$unknown = @($Only | Where-Object { $_ -notin $scenes.figures.number })
if($unknown.Count -gt 0) { throw "Unknown figure numbers: $unknown. Use -Figures '1,2,3' when invoking pwsh -File." }
$app = New-Object -ComObject PowerPoint.Application
$app.DisplayAlerts = 1
$previewRoot = Join-Path $taskRoot 'previews'
New-Item -ItemType Directory -Path $previewRoot -Force | Out-Null
$qaRoot = Join-Path (Split-Path -Parent $taskRoot) 'archive/production_checks'
New-Item -ItemType Directory -Path $qaRoot -Force | Out-Null

function Rgb([string]$hex) {
    $v = $hex.TrimStart('#')
    return [int]([Convert]::ToInt32($v.Substring(0,2),16) + 256 * [Convert]::ToInt32($v.Substring(2,2),16) + 65536 * [Convert]::ToInt32($v.Substring(4,2),16))
}

function Add-Object($slide, $o) {
    switch ($o.kind) {
        'text' {
            $shape = $slide.Shapes.AddTextbox(1, [single]$o.x, [single]$o.y, [single]$o.w, [single]$o.h)
            $shape.TextFrame.MarginLeft = 0
            $shape.TextFrame.MarginRight = 0
            $shape.TextFrame.MarginTop = 0
            $shape.TextFrame.MarginBottom = 0
            $shape.TextFrame.WordWrap = -1
            $shape.TextFrame.AutoSize = 0
            $shape.TextFrame2.AutoSize = 0
            $shape.TextFrame.VerticalAnchor = 3
            $tr = $shape.TextFrame.TextRange
            $tr.Text = $o.text
            $tr.Font.Name = $o.font
            $tr.Font.NameFarEast = $o.font
            $tr.Font.Size = [single]$o.size
            $tr.Font.Color.RGB = Rgb $o.color
            $tr.Font.Bold = $(if ($o.bold) { -1 } else { 0 })
            $tr.Font.Italic = $(if ($o.italic) { -1 } else { 0 })
            $tr.ParagraphFormat.Alignment = @{left=1;center=2;right=3}[$o.align]
            $tr.ParagraphFormat.SpaceBefore = 0
            $tr.ParagraphFormat.SpaceAfter = 0
            $tr.ParagraphFormat.Bullet.Visible = 0
            $shape.Line.Visible = 0
            if ($o.fill) { $shape.Fill.Solid(); $shape.Fill.ForeColor.RGB = Rgb $o.fill } else { $shape.Fill.Visible = 0 }
            # Font/auto-size changes can reset AddTextbox's height. Restore the
            # specified rectangle after all text properties have been set.
            $shape.Left = [single]$o.x
            $shape.Top = [single]$o.y
            $shape.Width = [single]$o.w
            $shape.Height = [single]$o.h
            if ($o.orientation -eq 'upward') { $shape.TextFrame2.Orientation = 3 }
            if ($o.rotation) { $shape.Rotation = [single]$o.rotation }
        }
        { $_ -in 'rect','ellipse' } {
            $type = $(if ($o.kind -eq 'ellipse') { 9 } else { 1 })
            $shape = $slide.Shapes.AddShape($type, [single]$o.x, [single]$o.y, [single]$o.w, [single]$o.h)
            if ($o.fill) { $shape.Fill.Solid(); $shape.Fill.ForeColor.RGB = Rgb $o.fill } else { $shape.Fill.Visible = 0 }
            if ($o.stroke) {
                $shape.Line.ForeColor.RGB = Rgb $o.stroke
                $shape.Line.Weight = [single]$o.weight
                if ($o.dash) { $shape.Line.DashStyle = 4 }
            } else { $shape.Line.Visible = 0 }
        }
        'line' {
            $shape = $slide.Shapes.AddLine([single]$o.x1,[single]$o.y1,[single]$o.x2,[single]$o.y2)
            $shape.Line.ForeColor.RGB = Rgb $o.color
            $shape.Line.Weight = [single]$o.weight
            if ($o.arrow) { $shape.Line.EndArrowheadStyle = 2; $shape.Line.EndArrowheadLength = 1; $shape.Line.EndArrowheadWidth = 1 }
            if ($o.dash) { $shape.Line.DashStyle = 4 }
        }
        'picture' {
            $path = Join-Path $taskRoot $o.path
            $shape = $slide.Shapes.AddPicture($path,0,-1,[single]$o.x,[single]$o.y,[single]$o.w,[single]$o.h)
            $shape.Line.Visible = 0
        }
        default { throw "Unknown object kind: $($o.kind)" }
    }
    $shape.Name = $o.name
    return $shape
}

function Add-FigureSlide($deck,$figure,[bool]$fit = $false) {
    $slide = $deck.Slides.Add($deck.Slides.Count+1,12)
    $slide.FollowMasterBackground = 0
    $slide.Background.Fill.Solid()
    $slide.Background.Fill.ForeColor.RGB = Rgb '#FFFFFF'
    $scale = 1.0
    $offsetX = 0.0
    $offsetY = 0.0
    if($fit -and ($figure.width -ne $deck.PageSetup.SlideWidth -or $figure.height -ne $deck.PageSetup.SlideHeight)) {
        $scale = [Math]::Min(($deck.PageSetup.SlideWidth-32)/$figure.width,($deck.PageSetup.SlideHeight-32)/$figure.height)
        $offsetX = ($deck.PageSetup.SlideWidth-$figure.width*$scale)/2
        $offsetY = ($deck.PageSetup.SlideHeight-$figure.height*$scale)/2
    }
    foreach($o in $figure.objects) {
        $draw = $o.PSObject.Copy()
        foreach($key in @('x','x1','x2')) { if($draw.PSObject.Properties[$key]) { $draw.$key = $o.$key*$scale+$offsetX } }
        foreach($key in @('y','y1','y2')) { if($draw.PSObject.Properties[$key]) { $draw.$key = $o.$key*$scale+$offsetY } }
        foreach($key in @('w','h','size','weight')) { if($draw.PSObject.Properties[$key]) { $draw.$key = $o.$key*$scale } }
        Add-Object $slide $draw | Out-Null
    }
    $slide.Tags.Add('FigureNumber',[string]$figure.number)
    foreach($shape in $slide.NotesPage.Shapes) {
        if($shape.Type -eq 14 -and $shape.PlaceholderFormat.Type -eq 2) {
            $shape.TextFrame.TextRange.Text = $figure.notes
            $shape.TextFrame.TextRange.Font.Name = 'Arial'
            $shape.TextFrame.TextRange.Font.Size = 10
        }
    }
    return $slide
}

$report = @()
$selected = @($scenes.figures | Where-Object { $Only.Count -eq 0 -or $_.number -in $Only })
foreach($figure in $selected) {
    $deck = $app.Presentations.Add(0)
    $deck.PageSetup.SlideWidth = [single]$figure.width
    $deck.PageSetup.SlideHeight = [single]$figure.height
    $slide = Add-FigureSlide $deck $figure
    $path = Join-Path $taskRoot "$($figure.stem).pptx"
    $deck.SaveAs($path,24)
    $previewHeight = [int][Math]::Round(1920*$figure.height/$figure.width)
    $slide.Export((Join-Path $previewRoot "$($figure.stem).png"),'PNG',1920,$previewHeight)
    $overflow = @()
    foreach($shape in $slide.Shapes) {
        if($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
            if($shape.Rotation -eq 0 -and $shape.TextFrame2.Orientation -eq 1 -and ($shape.TextFrame2.TextRange.BoundHeight -gt $shape.Height+1.5 -or $shape.TextFrame2.TextRange.BoundWidth -gt $shape.Width+1.5)) {
                $overflow += [pscustomobject]@{name=$shape.Name;text=$shape.TextFrame.TextRange.Text;w=$shape.Width;h=$shape.Height;boundW=$shape.TextFrame2.TextRange.BoundWidth;boundH=$shape.TextFrame2.TextRange.BoundHeight}
            }
        }
    }
    $report += [pscustomobject]@{figure=$figure.number;path=$path;objects=$slide.Shapes.Count;overflow=$overflow}
    $deck.Close()
    Write-Output "Created Fig. $($figure.number): $($figure.stem).pptx"
}

# PowerPoint has one page size per file. Fit revised figures to the review
# canvas while preserving every untouched slide and its editable objects.
if($Only.Count -eq 0 -or $RefreshReview) {
    $reviewPath = Join-Path $taskRoot 'all_figures_editable.pptx'
    if($Only.Count -gt 0 -and (Test-Path -LiteralPath $reviewPath)) {
        $review = $app.Presentations.Open($reviewPath,0,0,0)
        $hasIndex = $review.Slides.Item(1).Tags.Item('FigureIndex') -eq 'true'
        if($hasIndex) { $review.Slides.Item(1).Delete() }
        $positions = @()
        for($i=0;$i -lt $scenes.figures.Count;$i++) {
            if($scenes.figures[$i].number -in $Only) { $positions += ($i+1) }
        }
        foreach($position in ($positions | Sort-Object -Descending)) { $review.Slides.Item($position).Delete() }
        foreach($position in ($positions | Sort-Object)) {
            $newSlide = Add-FigureSlide $review $scenes.figures[$position-1] $true
            $newSlide.MoveTo($position)
        }
    } else {
        $review = $app.Presentations.Add(0)
        $review.PageSetup.SlideWidth = 960
        $review.PageSetup.SlideHeight = 640
        foreach($figure in $scenes.figures) { Add-FigureSlide $review $figure $true | Out-Null }
    }
    $indexSlide = $review.Slides.Add($review.Slides.Count+1,12)
    $indexSlide.MoveTo(1)
    $indexSlide.Tags.Add('FigureIndex','true')
    $indexSlide.FollowMasterBackground = 0
    $indexSlide.Background.Fill.Solid()
    $indexSlide.Background.Fill.ForeColor.RGB = Rgb '#FFFFFF'
    function Index-Text($x,$y,$w,$h,$value,$size=14,$font='Arial',$bold=$false) {
        return Add-Object $indexSlide ([pscustomobject]@{kind='text';name=('index_'+$indexSlide.Shapes.Count);x=$x;y=$y;w=$w;h=$h;text=$value;size=$size;font=$font;bold=$bold;italic=$false;align='left';color='#202020';fill=$null;rotation=0})
    }
    Index-Text 52 44 850 38 'Figure index' 25 'Times New Roman' | Out-Null
    Index-Text 52 89 850 25 'v5 editable figure collection' 12 | Out-Null
    Index-Text 52 139 100 24 'Figure' 12 'Arial' $true | Out-Null
    Index-Text 161 139 660 24 'Title' 12 'Arial' $true | Out-Null
    Index-Text 858 139 65 24 'Page' 12 'Arial' $true | Out-Null
    Add-Object $indexSlide ([pscustomobject]@{kind='line';name='index_rule';x1=52;y1=170;x2=908;y2=170;color='#888888';weight=.6;arrow=$false;dash=$false}) | Out-Null
    for($i=0;$i -lt $scenes.figures.Count;$i++) {
        $figure = $scenes.figures[$i]
        $y = 181+$i*40
        Index-Text 52 $y 99 30 ([string]$figure.number) 13 | Out-Null
        $link = Index-Text 161 $y 665 30 $figure.title 12.5
        $destination = $review.Slides.Item($i+2)
        $link.ActionSettings.Item(1).Action = 7
        $link.ActionSettings.Item(1).Hyperlink.SubAddress = "$($destination.SlideID),$($i+2),$($destination.Name)"
        Index-Text 858 $y 50 30 ([string]($i+2)) 13 | Out-Null
    }
    Index-Text 52 574 850 26 'Click a title to open its figure in Slide Show.' 11 | Out-Null
    $review.SaveAs($reviewPath,24)
    $indexSlide.Export((Join-Path $previewRoot 'figure_index.png'),'PNG',1920,1280)
    $review.Close()
}
$reportPath = Join-Path $qaRoot 'layout_check.json'
if($Only.Count -gt 0 -and (Test-Path -LiteralPath $reportPath)) {
    $previous = @(Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    $report = @($previous | Where-Object { $_.figure -notin $Only }) + $report
    $report = @($report | Sort-Object figure)
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
# Leave the user's PowerPoint session and existing decks open.
$report | Select-Object figure,objects,@{n='overflow';e={$_.overflow.Count}} | Format-Table
