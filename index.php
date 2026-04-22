<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
session_start();

$host = 'localhost';
$user = 'root';
$password = '';
$database = 'app';

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

if (!isset($_SESSION['cart'])) {
    $_SESSION['cart'] = [];
}

function getStock($conn, $menu_id) {
    $stmt = $conn->prepare("SELECT stock FROM menu WHERE id = ?");
    $stmt->bind_param("i", $menu_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $row = $result->fetch_assoc();
    return $row ? (int)$row['stock'] : 0;
}

function getImageSrc($db_path) {
    if (empty($db_path)) return null;
    if (file_exists($db_path)) return htmlspecialchars($db_path);
    $alt_path = "menu_images/" . basename($db_path);
    if (file_exists($alt_path)) return htmlspecialchars($alt_path);
    if (file_exists(basename($db_path))) return htmlspecialchars(basename($db_path));
    return null;
}

function generateOrderCode($conn) {
    $result = $conn->query("SELECT MAX(CAST(order_code AS UNSIGNED)) AS last_num FROM orders WHERE order_code REGEXP '^[0-9]+$'");
    $row = $result->fetch_assoc();
    $next = ((int)$row['last_num']) + 1;
    return str_pad($next, 5, '0', STR_PAD_LEFT);
}

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['add_to_cart'])) {
    $menu_id = $_POST['menu_id'];
    $quantity = (int)$_POST['quantity'];
    $current_stock = getStock($conn, $menu_id);
    if ($quantity > $current_stock) {
        $_SESSION['error'] = "Sorry, only $current_stock item(s) available.";
        header("Location: index.php");
        exit;
    }
    $stmt = $conn->prepare("SELECT id, name, price FROM menu WHERE id = ?");
    $stmt->bind_param("i", $menu_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $item = $result->fetch_assoc();
    if ($item) {
        if (isset($_SESSION['cart'][$menu_id])) {
            $new_qty = $_SESSION['cart'][$menu_id]['quantity'] + $quantity;
            if ($new_qty > $current_stock) {
                $_SESSION['error'] = "Cannot add $quantity. Total would exceed stock ($current_stock).";
                header("Location: index.php");
                exit;
            }
            $_SESSION['cart'][$menu_id]['quantity'] += $quantity;
        } else {
            $_SESSION['cart'][$menu_id] = [
                'name' => $item['name'],
                'price' => $item['price'],
                'quantity' => $quantity
            ];
        }
    }
    header("Location: index.php");
    exit;
}

if (isset($_GET['remove'])) {
    $id = $_GET['remove'];
    unset($_SESSION['cart'][$id]);
    header("Location: index.php");
    exit;
}

if (isset($_POST['checkout'])) {
    if (empty($_SESSION['cart'])) {
        $error = "Your cart is empty.";
    } else {
        $stock_ok = true;
        $error_items = [];
        foreach ($_SESSION['cart'] as $menu_id => $item) {
            $current_stock = getStock($conn, $menu_id);
            if ($item['quantity'] > $current_stock) {
                $stock_ok = false;
                $error_items[] = "{$item['name']} (only $current_stock left)";
            }
        }
        if (!$stock_ok) {
            $error = "Stock insufficient for: " . implode(", ", $error_items);
        } else {
            $total = 0;
            foreach ($_SESSION['cart'] as $item) {
                $total += $item['price'] * $item['quantity'];
            }

            // --- Sequential order code: 00001, 00002, 00003 ... ---
            $order_code = generateOrderCode($conn);
            // -------------------------------------------------------

            $stmt = $conn->prepare("INSERT INTO orders (order_code, total_amount) VALUES (?, ?)");
            $stmt->bind_param("sd", $order_code, $total);
            $stmt->execute();
            $order_id = $stmt->insert_id;
            $stmt_item = $conn->prepare("INSERT INTO order_items (order_id, menu_id, quantity, price) VALUES (?, ?, ?, ?)");
            $stmt_update_stock = $conn->prepare("UPDATE menu SET stock = stock - ? WHERE id = ?");
            foreach ($_SESSION['cart'] as $menu_id => $item) {
                $stmt_item->bind_param("iiid", $order_id, $menu_id, $item['quantity'], $item['price']);
                $stmt_item->execute();
                $stmt_update_stock->bind_param("ii", $item['quantity'], $menu_id);
                $stmt_update_stock->execute();
            }

            // ========== OFFLINE QR CODE GENERATION (phpqrcode) ==========
            require_once 'phpqrcode/phpqrcode.php';
            $qr_data = "http://" . $_SERVER['HTTP_HOST'] . dirname($_SERVER['SCRIPT_NAME']) . "/staff_scan.php?code=" . $order_code;
            $qr_filename = "qr_codes/" . $order_code . ".png";
            if (!is_dir('qr_codes')) mkdir('qr_codes', 0777, true);
            QRcode::png($qr_data, $qr_filename, QR_ECLEVEL_L, 10);
            // ========== END OFFLINE QR ==========

            $_SESSION['cart'] = [];
            header("Location: index.php?success=1&order_code=" . $order_code);
            exit;
        }
    }
}

if (isset($_SESSION['error'])) {
    $error = $_SESSION['error'];
    unset($_SESSION['error']);
}

$cart_count = 0;
$cart_total = 0;
foreach ($_SESSION['cart'] as $item) {
    $cart_count += $item['quantity'];
    $cart_total += $item['price'] * $item['quantity'];
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snack in Save 9Nueve</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0d0d0d;
            --surface: #161616;
            --surface2: #1f1f1f;
            --border: #2a2a2a;
            --accent: #f97316;
            --accent2: #fb923c;
            --gold: #f59e0b;
            --text: #f5f5f5;
            --text2: #a3a3a3;
            --text3: #525252;
            --success: #22c55e;
            --danger: #ef4444;
            --radius: 20px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--bg);
            font-family: 'DM Sans', sans-serif;
            color: var(--text);
            min-height: 100vh;
        }

        .topnav {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(13,13,13,0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
        }
        .brand { display: flex; flex-direction: column; line-height: 1.1; }
        .brand-name {
            font-family: 'Playfair Display', serif;
            font-size: 1.15rem;
            font-weight: 900;
            color: var(--accent);
            letter-spacing: -0.5px;
        }
        .brand-sub {
            font-size: 0.65rem;
            color: var(--text3);
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .nav-right { display: flex; align-items: center; gap: 12px; }
        .cart-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--accent);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 40px;
            font-family: 'DM Sans', sans-serif;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .cart-pill:hover { background: var(--accent2); transform: scale(0.97); }
        .cart-pill .badge {
            background: white;
            color: var(--accent);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.72rem;
            font-weight: 700;
        }

        .hero {
            background: linear-gradient(135deg, #1a0a00 0%, #0d0d0d 60%);
            padding: 56px 24px 40px;
            text-align: center;
            border-bottom: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(ellipse at 50% 0%, rgba(249,115,22,0.15) 0%, transparent 70%);
        }
        .hero-label {
            display: inline-block;
            background: rgba(249,115,22,0.15);
            border: 1px solid rgba(249,115,22,0.3);
            color: var(--accent);
            font-size: 0.7rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            padding: 5px 14px;
            border-radius: 40px;
            margin-bottom: 16px;
        }
        .hero h1 {
            font-family: 'Playfair Display', serif;
            font-size: clamp(2rem, 7vw, 3.5rem);
            font-weight: 900;
            line-height: 1.05;
            margin-bottom: 12px;
            position: relative;
        }
        .hero h1 span { color: var(--accent); }
        .hero p { color: var(--text2); font-size: 0.95rem; position: relative; }

        .main-wrap {
            max-width: 1320px;
            margin: 0 auto;
            padding: 32px 20px;
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 28px;
            align-items: start;
        }
        .section-label {
            font-size: 0.65rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 6px;
        }
        .section-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 24px;
        }
        .menu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
            gap: 16px;
        }
        .menu-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            transition: all 0.25s;
            position: relative;
        }
        .menu-card:hover {
            border-color: var(--accent);
            transform: translateY(-4px);
            box-shadow: 0 20px 40px -12px rgba(249,115,22,0.2);
        }
        .menu-card.out-of-stock { opacity: 0.5; pointer-events: none; }
        .card-img-wrap {
            width: 100%;
            height: 130px;
            overflow: hidden;
            background: var(--surface2);
            position: relative;
        }
        .card-img-wrap img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }
        .menu-card:hover .card-img-wrap img { transform: scale(1.06); }
        .card-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #1f1f1f, #2a2a2a);
        }
        .out-badge {
            position: absolute;
            top: 8px; left: 8px;
            background: var(--danger);
            color: white;
            font-size: 0.6rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 40px;
        }
        .card-body { padding: 12px 14px 14px; }
        .card-name {
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 4px;
            color: var(--text);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .card-price {
            font-family: 'Playfair Display', serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 6px;
        }
        .card-stock { font-size: 0.7rem; color: var(--text3); margin-bottom: 10px; }
        .card-stock.low { color: var(--gold); }
        .add-row { display: flex; gap: 6px; align-items: center; }
        .qty-input {
            width: 52px;
            background: var(--surface2);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 7px 8px;
            border-radius: 10px;
            text-align: center;
            font-family: 'DM Sans', sans-serif;
            font-size: 0.85rem;
        }
        .qty-input:focus { outline: none; border-color: var(--accent); }
        .btn-add {
            flex: 1;
            background: var(--accent);
            color: white;
            border: none;
            padding: 8px 10px;
            border-radius: 10px;
            font-family: 'DM Sans', sans-serif;
            font-weight: 600;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-add:hover { background: var(--accent2); }

        .cart-sidebar {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            overflow: hidden;
            position: sticky;
            top: 80px;
        }
        .cart-header {
            padding: 20px 22px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .cart-header-left h2 { font-family: 'Playfair Display', serif; font-size: 1.2rem; }
        .cart-header-left p { font-size: 0.75rem; color: var(--text2); margin-top: 2px; }
        .cart-count-badge {
            background: var(--accent);
            color: white;
            border-radius: 50%;
            width: 28px; height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.8rem;
        }
        .cart-items { padding: 16px 22px; max-height: 320px; overflow-y: auto; }
        .cart-items::-webkit-scrollbar { width: 4px; }
        .cart-items::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        .cart-empty { text-align: center; color: var(--text3); padding: 32px 0; font-size: 0.85rem; }
        .cart-empty .empty-icon { font-size: 2.5rem; margin-bottom: 8px; }
        .cart-row {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
            animation: fadeIn 0.2s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        .cart-row:last-child { border-bottom: none; }
        .cart-row-info { flex: 1; min-width: 0; }
        .cart-row-name { font-size: 0.85rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .cart-row-detail { font-size: 0.75rem; color: var(--text2); margin-top: 2px; }
        .cart-row-subtotal { font-size: 0.85rem; font-weight: 700; color: var(--accent); white-space: nowrap; }
        .btn-remove {
            background: none;
            border: none;
            color: var(--text3);
            cursor: pointer;
            font-size: 1rem;
            padding: 2px 4px;
            transition: color 0.15s;
            text-decoration: none;
        }
        .btn-remove:hover { color: var(--danger); }
        .cart-footer { padding: 16px 22px; border-top: 1px solid var(--border); }
        .total-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .total-label { font-size: 0.8rem; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }
        .total-amount {
            font-family: 'Playfair Display', serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--accent);
        }
        .btn-checkout {
            width: 100%;
            background: linear-gradient(135deg, var(--accent), #ea580c);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 14px;
            font-family: 'DM Sans', sans-serif;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-checkout:hover { transform: scale(0.98); box-shadow: 0 8px 20px rgba(249,115,22,0.3); }
        .error-msg {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            color: #fca5a5;
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 0.8rem;
            margin-top: 10px;
        }

        .success-wrap { max-width: 520px; margin: 60px auto; padding: 0 20px; text-align: center; }
        .success-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 40px 32px;
        }
        .success-icon {
            width: 64px; height: 64px;
            background: rgba(34,197,94,0.15);
            border: 2px solid var(--success);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            margin: 0 auto 20px;
        }
        .success-card h2 { font-family: 'Playfair Display', serif; font-size: 1.8rem; margin-bottom: 8px; }
        .success-card p { color: var(--text2); font-size: 0.9rem; margin-bottom: 6px; }
        .order-code-badge {
            display: inline-block;
            background: rgba(249,115,22,0.1);
            border: 1px solid rgba(249,115,22,0.3);
            color: var(--accent);
            font-weight: 700;
            padding: 6px 18px;
            border-radius: 40px;
            margin: 12px 0 28px;
            letter-spacing: 1px;
        }
        .qr-wrap {
            background: white;
            border-radius: 16px;
            padding: 16px;
            display: inline-block;
            margin-bottom: 24px;
        }
        .qr-wrap img { display: block; border-radius: 8px; }
        .qr-hint { font-size: 0.75rem; color: var(--text3); margin-bottom: 24px; }
        .btn-new-order {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--accent);
            color: white;
            padding: 12px 28px;
            border-radius: 40px;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .btn-new-order:hover { background: var(--accent2); transform: scale(0.97); }

        .orders-wrap { max-width: 1320px; margin: 0 auto 40px; padding: 0 20px; }
        .table-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            overflow: hidden;
        }
        .table-card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .table-card-header h2 { font-family: 'Playfair Display', serif; font-size: 1.2rem; }
        .table-card-header span { font-size: 0.75rem; color: var(--text2); }
        .orders-table { width: 100%; border-collapse: collapse; }
        .orders-table thead th {
            padding: 12px 18px;
            text-align: left;
            font-size: 0.68rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text3);
            background: var(--surface);
            border-bottom: 1px solid var(--border);
        }
        .orders-table tbody td {
            padding: 14px 18px;
            font-size: 0.85rem;
            border-bottom: 1px solid rgba(42,42,42,0.5);
            vertical-align: middle;
        }
        .orders-table tbody tr:last-child td { border-bottom: none; }
        .orders-table tbody tr:hover td { background: var(--surface2); }
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 40px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-pending { background: rgba(245,158,11,0.15); color: var(--gold); border: 1px solid rgba(245,158,11,0.3); }
        .status-done { background: rgba(34,197,94,0.1); color: var(--success); border: 1px solid rgba(34,197,94,0.25); }
        .order-amount { color: var(--accent); font-weight: 700; font-family: 'Playfair Display', serif; }
        .qr-mini { width: 48px; height: 48px; border-radius: 6px; background: white; padding: 2px; }
        .empty-table { text-align: center; color: var(--text3); padding: 40px; font-size: 0.85rem; }

        @media (max-width: 900px) {
            .main-wrap { grid-template-columns: 1fr; }
            .cart-sidebar { position: static; }
        }
        @media (max-width: 500px) {
            .menu-grid { grid-template-columns: repeat(2, 1fr); }
            .hero { padding: 40px 16px 32px; }
            .main-wrap { padding: 20px 12px; }
            .orders-wrap { padding: 0 12px; }
        }
    </style>
</head>
<body>

<nav class="topnav">
    <div class="brand">
        <span class="brand-name">Snack in Save</span>
        <span class="brand-sub">9Nueve</span>
    </div>
    <div class="nav-right">
        <?php if (!isset($_GET['success'])): ?>
        <button class="cart-pill" onclick="document.querySelector('.cart-sidebar').scrollIntoView({behavior:'smooth'})">
            <span class="cart-icon"></span>
            Your Order
            <span class="badge"><?php echo $cart_count; ?></span>
        </button>
        <?php endif; ?>
    </div>
</nav>

<div class="hero">
    <div class="hero-label">Self-Order Kiosk</div>
    <h1>Order Fresh,<br><span>Eat Happy</span></h1>
    <p>Pick your items · Place order · Show QR to staff</p>
</div>

<?php if (isset($_GET['success']) && $_GET['success'] == 1 && isset($_GET['order_code'])):
    $order_code = $_GET['order_code'];
?>
<div class="success-wrap">
    <div class="success-card">
        <div class="success-icon">✓</div>
        <h2>Order Placed!</h2>
        <p>Your order has been received.</p>
        <p>Show this QR code to our staff.</p>
        <div class="order-code-badge"><?php echo htmlspecialchars($order_code); ?></div>
        <br>
        <div class="qr-wrap">
            <?php
            $qr_file = "qr_codes/" . $order_code . ".png";
            if (file_exists($qr_file)) {
                $qr_img_src = htmlspecialchars($qr_file);
            } else {
                $qr_data_fallback = "http://" . $_SERVER['HTTP_HOST'] . dirname($_SERVER['SCRIPT_NAME']) . "/staff_scan.php?code=" . $order_code;
                $qr_img_src = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" . urlencode($qr_data_fallback);
            }
            ?>
            <img src="<?php echo $qr_img_src; ?>" width="180" height="180" alt="QR Code">
        </div>
        <div class="qr-hint">📱 Scan this QR code at the counter</div>
        <a href="index.php" class="btn-new-order">+ New Order</a>
    </div>
</div>

<?php else: ?>

<div class="main-wrap">
    <div>
        <div class="section-label">What we serve</div>
        <div class="section-title">Menu</div>
        <div class="menu-grid">
            <?php
            $result = $conn->query("SELECT id, name, price, image_path, stock FROM menu ORDER BY name");
            if ($result && $result->num_rows > 0):
                while ($row = $result->fetch_assoc()):
                    $img_src = getImageSrc($row['image_path']);
                    $is_out = (int)$row['stock'] === 0;
                    $is_low = (int)$row['stock'] <= 3 && !$is_out;
            ?>
            <div class="menu-card <?php echo $is_out ? 'out-of-stock' : ''; ?>">
                <div class="card-img-wrap">
                    <?php if ($img_src): ?>
                        <img src="<?php echo $img_src; ?>" alt="<?php echo htmlspecialchars($row['name']); ?>">
                    <?php else: ?>
                        <div class="card-placeholder"></div>
                    <?php endif; ?>
                    <?php if ($is_out): ?><span class="out-badge">Sold Out</span><?php endif; ?>
                </div>
                <div class="card-body">
                    <div class="card-name"><?php echo htmlspecialchars($row['name']); ?></div>
                    <div class="card-price">₱<?php echo number_format($row['price'], 2); ?></div>
                    <div class="card-stock <?php echo $is_low ? 'low' : ''; ?>">
                        <?php echo $is_low ? '⚠ ' : ''; ?>
                        Stock: <?php echo (int)$row['stock']; ?>
                    </div>
                    <?php if (!$is_out): ?>
                    <form method="post" class="add-row">
                        <input type="hidden" name="menu_id" value="<?php echo $row['id']; ?>">
                        <input type="number" name="quantity" class="qty-input" value="1" min="1" max="<?php echo (int)$row['stock']; ?>">
                        <button type="submit" name="add_to_cart" class="btn-add">+ Add</button>
                    </form>
                    <?php endif; ?>
                </div>
            </div>
            <?php endwhile;
            else: ?>
                <div style="color:var(--text2);padding:32px 0;">No items available right now.</div>
            <?php endif; ?>
        </div>
    </div>

    <div>
        <div class="cart-sidebar">
            <div class="cart-header">
                <div class="cart-header-left">
                    <h2>Your Order</h2>
                    <p><?php echo $cart_count; ?> item<?php echo $cart_count !== 1 ? 's' : ''; ?> selected</p>
                </div>
                <div class="cart-count-badge"><?php echo $cart_count; ?></div>
            </div>
            <div class="cart-items">
                <?php if (empty($_SESSION['cart'])): ?>
                <div class="cart-empty">
                    <div class="empty-icon">🧺</div>
                    <div>Your cart is empty</div>
                    <div style="font-size:0.75rem;margin-top:4px;">Add items from the menu</div>
                </div>
                <?php else:
                    foreach ($_SESSION['cart'] as $id => $item):
                        $subtotal = $item['price'] * $item['quantity'];
                ?>
                <div class="cart-row">
                    <div class="cart-row-info">
                        <div class="cart-row-name"><?php echo htmlspecialchars($item['name']); ?></div>
                        <div class="cart-row-detail">₱<?php echo number_format($item['price'], 2); ?> × <?php echo $item['quantity']; ?></div>
                    </div>
                    <div class="cart-row-subtotal">₱<?php echo number_format($subtotal, 2); ?></div>
                    <a href="?remove=<?php echo $id; ?>" class="btn-remove" title="Remove">✕</a>
                </div>
                <?php endforeach; endif; ?>
            </div>
            <div class="cart-footer">
                <div class="total-line">
                    <span class="total-label">Total</span>
                    <span class="total-amount">₱<?php echo number_format($cart_total, 2); ?></span>
                </div>
                <?php if (!empty($_SESSION['cart'])): ?>
                <form method="post">
                    <button type="submit" name="checkout" class="btn-checkout">
                        🧾 Place Order & Get QR
                    </button>
                </form>
                <?php endif; ?>
                <?php if (isset($error)): ?>
                <div class="error-msg">⚠ <?php echo htmlspecialchars($error); ?></div>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<?php
$orders_result = $conn->query("
    SELECT o.id, o.order_code, o.total_amount, o.created_at,
           GROUP_CONCAT(m.name ORDER BY m.name SEPARATOR ', ') AS items,
           o.status
    FROM orders o
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN menu m ON m.id = oi.menu_id
    GROUP BY o.id
    ORDER BY o.created_at DESC
    LIMIT 20
");
?>
<div class="orders-wrap">
    <div class="table-card">
        <div class="table-card-header">
            <h2>Recent Orders</h2>
            <span>Last 20 orders</span>
        </div>
        <?php if ($orders_result && $orders_result->num_rows > 0): ?>
        <div style="overflow-x:auto;">
            <table class="orders-table">
                <thead>
                    <tr>
                        <th>QR</th>
                        <th>Order Code</th>
                        <th>Items</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                <?php while ($ord = $orders_result->fetch_assoc()):
                    $qr_file = "qr_codes/" . $ord['order_code'] . ".png";
                    $status = isset($ord['status']) ? $ord['status'] : 'pending';
                ?>
                <tr>
                    <td>
                        <?php if (file_exists($qr_file)): ?>
                        <img src="<?php echo htmlspecialchars($qr_file); ?>" class="qr-mini" alt="QR">
                        <?php else: ?>
                        <span style="color:var(--text3);font-size:0.75rem;">—</span>
                        <?php endif; ?>
                    </td>
                    <td style="font-family:monospace;font-size:0.78rem;color:var(--accent);"><?php echo htmlspecialchars($ord['order_code']); ?></td>
                    <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text2);font-size:0.8rem;"><?php echo htmlspecialchars($ord['items'] ?? '—'); ?></td>
                    <td class="order-amount">₱<?php echo number_format($ord['total_amount'], 2); ?></td>
                    <td>
                        <span class="status-badge status-<?php echo htmlspecialchars($status); ?>">
                            <?php echo ucfirst(htmlspecialchars($status)); ?>
                        </span>
                    </td>
                    <td style="color:var(--text2);font-size:0.78rem;"><?php echo date('M j, g:i A', strtotime($ord['created_at'])); ?></td>
                </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
        </div>
        <?php else: ?>
        <div class="empty-table">No orders yet.</div>
        <?php endif; ?>
    </div>
</div>

<?php endif; ?>

</body>
</html>