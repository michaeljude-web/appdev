<?php
session_start();
header('Content-Type: application/json');

$host = 'localhost';
$user = 'root';
$password = '';
$database = 'app';

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    echo json_encode(['success' => false, 'error' => 'Database connection failed']);
    exit;
}

function getStock($conn, $menu_id) {
    $stmt = $conn->prepare("SELECT stock FROM menu WHERE id = ?");
    $stmt->bind_param("i", $menu_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $row = $result->fetch_assoc();
    return $row ? (int)$row['stock'] : 0;
}

if (!isset($_SESSION['cart'])) {
    $_SESSION['cart'] = [];
}

$id = isset($_POST['id']) ? (int)$_POST['id'] : 0;
$action = isset($_POST['action']) ? $_POST['action'] : '';

if (!$id) {
    echo json_encode(['success' => false, 'error' => 'Invalid item ID']);
    exit;
}

$stock = getStock($conn, $id);

if ($action === 'inc') {
    $current = isset($_SESSION['cart'][$id]) ? $_SESSION['cart'][$id]['quantity'] : 0;
    if ($current + 1 <= $stock) {
        if (!isset($_SESSION['cart'][$id])) {
            $stmt = $conn->prepare("SELECT name, price FROM menu WHERE id = ?");
            $stmt->bind_param("i", $id);
            $stmt->execute();
            $item = $stmt->get_result()->fetch_assoc();
            if ($item) {
                $_SESSION['cart'][$id] = [
                    'name' => $item['name'],
                    'price' => (float)$item['price'],
                    'quantity' => 1
                ];
            } else {
                echo json_encode(['success' => false, 'error' => 'Item not found']);
                exit;
            }
        } else {
            $_SESSION['cart'][$id]['quantity']++;
        }
    } else {
        echo json_encode(['success' => false, 'error' => 'Stock limit reached']);
        exit;
    }
} elseif ($action === 'dec') {
    if (isset($_SESSION['cart'][$id])) {
        $_SESSION['cart'][$id]['quantity']--;
        if ($_SESSION['cart'][$id]['quantity'] <= 0) {
            unset($_SESSION['cart'][$id]);
        }
    }
} elseif ($action === 'remove') {
    unset($_SESSION['cart'][$id]);
} else {
    echo json_encode(['success' => false, 'error' => 'Invalid action']);
    exit;
}

echo json_encode([
    'success' => true,
    'cart' => $_SESSION['cart']
]);